import re
from io import BytesIO

import pandas as pd

CHUNGNAM_REGIONS = [
    "천안", "아산", "공주", "보령", "서산", "논산", "계룡", "당진",
    "금산", "부여", "서천", "청양", "홍성", "예산", "태안",
]
DEFAULT_TARGET_AMOUNT = 500000
CONTRACT_METHODS = ["수의계약", "입찰", "조달구매"]
COMPETITION_METHODS = [
    "1인수의(단일견적)", "2인수의(공개견적)", "제3자단가",
    "다수공급자2단계경쟁(MAS)", "우수조달", "중앙조달",
    "자체(제한경쟁)", "자체(일반경쟁)", "협상", "2단계(규격가격동시)",
]
PURCHASE_PURPOSES = ["교육용", "도서(간행물 등)", "그 외"]

FALLBACK_COLS = {
    "type": 1,
    "contract_method": 2,
    "competition_method": 3,
    "contract_name": 4,
    "contract_date": 5,
    "amount": 6,
    "company": 16,
    "biz": 18,
    "address": 20,
}

HEADER_ALIASES = {
    "type": ["목적물", "목적물별", "계약구분", "구분", "계약종류"],
    "contract_method": ["계약방법", "계약 방식", "계약방식"],
    "competition_method": ["견적/경쟁방법", "견적경쟁방법", "견적방법", "경쟁방법"],
    "contract_name": ["계약명", "계약건명", "건명", "품명", "사업명"],
    "contract_date": ["계약일자", "계약일", "계약체결일", "계약일시"],
    "amount": ["계약금액(원)", "계약금액", "집행금액", "금액"],
    "company": ["업체명", "계약업체명", "계약상대자", "계약상대자명", "상호"],
    "biz": ["사업자등록번호", "사업자번호", "사업자 등록번호"],
    "address": ["주소", "업체주소", "사업장주소", "소재지주소"],
    "institution": ["계약기관", "기관명(학교명)", "기관명", "학교명", "기관(학교)명", "기관학교명"],
    "school_level": ["급별", "학교급", "기관급별"],
}


def normalize_header(value):
    return re.sub(r"[\s\n\r\t()（）\[\]{}_/·ㆍ.-]+", "", str(value or "")).lower()


def normalize_biz_no(value):
    if pd.isna(value):
        return ""
    digits = re.sub(r"\D", "", re.sub(r"\.0$", "", str(value).strip()))
    return digits if len(digits) == 10 else ""


def normalize_contract_type(value):
    text = str(value or "").strip()
    for key in ("공사", "용역", "물품"):
        if key in text:
            return key
    return text


def missing_address_mask(series):
    text = series.astype(str).str.strip()
    return series.isna() | text.eq("") | text.str.lower().isin(["nan", "none", "null"])


def find_source_col(headers, key):
    normalized = [normalize_header(h) for h in headers]
    for alias in HEADER_ALIASES.get(key, []):
        target = normalize_header(alias)
        for i, header in enumerate(normalized):
            if header == target or (target and target in header):
                return i
    fallback = FALLBACK_COLS.get(key)
    return fallback if fallback is not None and fallback < len(headers) else None


def source_col(headers, key):
    found = find_source_col(headers, key)
    return FALLBACK_COLS.get(key) if found is None else found


def _load_one(file_bytes):
    df = pd.read_excel(BytesIO(file_bytes))
    headers = [str(c).strip() for c in df.columns]
    df.columns = range(df.shape[1])
    if df.shape[1] < 21:
        df = df.reindex(columns=range(21))
        headers.extend([f"열{i + 1}" for i in range(len(headers), 21)])
    return df, headers


def combine_workbooks(file_payloads):
    if not file_payloads:
        raise ValueError("엑셀 파일이 없습니다.")

    loaded = [_load_one(payload) for payload in file_payloads]
    frames = [item[0] for item in loaded]
    headers = list(loaded[0][1])

    max_cols = max(frame.shape[1] for frame in frames)
    frames = [frame.reindex(columns=range(max_cols)) for frame in frames]
    if len(headers) < max_cols:
        headers.extend([f"열{i + 1}" for i in range(len(headers), max_cols)])

    return pd.concat(frames, ignore_index=True), headers


def _detect_region(df, address_col):
    if address_col is None or address_col >= df.shape[1]:
        return CHUNGNAM_REGIONS[0], 0

    counts = {region: 0 for region in CHUNGNAM_REGIONS}
    for value in df.iloc[:, address_col].dropna():
        text = str(value).strip()
        if not text:
            continue
        for region in CHUNGNAM_REGIONS:
            if region in text:
                counts[region] += 1
                break

    return max(counts.items(), key=lambda item: item[1])


def safe_value(row, idx, default=""):
    if idx is None or idx >= len(row):
        return default
    value = row.iloc[idx]
    return default if pd.isna(value) else value


def first_nonblank(series, skip_values=None):
    skip = {re.sub(r"\s+", "", str(v)) for v in (skip_values or [])}
    for value in series:
        if pd.isna(value):
            continue
        text = str(value).strip()
        compact = re.sub(r"\s+", "", text)
        if not text or text.lower() in ("nan", "none", "null") or compact in skip:
            continue
        return text
    return ""


def classify_school_level(institution):
    name = re.sub(r"\s+", "", str(institution or "").strip())
    if not name:
        return ""
    if name == "충청남도교육청":
        return "본청"
    if "지원청" in name:
        return "교육지원청"
    if "유치원" in name:
        return "학교(유)"
    if "초등학교" in name:
        return "학교(초)"
    if "중학교" in name:
        return "학교(중)"
    if "고등학교" in name:
        return "학교(고)"
    return "직속기관"


def extract_source_metadata(df, headers):
    inst_col = 8 if df.shape[1] > 8 else find_source_col(headers, "institution")
    institution = (
        first_nonblank(df.iloc[:, inst_col], skip_values=["계약기관"])
        if inst_col is not None and inst_col < df.shape[1]
        else ""
    )
    return institution, classify_school_level(institution)


def normalize_contract_method(value):
    text = re.sub(r"\s+", "", str(value or "").strip())
    if not text or text.lower() in ("nan", "none", "null"):
        return ""
    if "수의" in text:
        return "수의계약"
    if "입찰" in text:
        return "입찰"
    if "조달" in text:
        return "조달구매"
    return str(value).strip()


def map_competition_method(raw_value, contract_method):
    text = re.sub(r"\s+", "", str(raw_value or "").strip())
    if text and text.lower() not in ("nan", "none", "null"):
        if "단일견적" in text or "1인수의" in text or "1인견적" in text:
            return "1인수의(단일견적)"
        if "2인수의" in text or "2인견적" in text or "2인이상" in text or "공개견적" in text:
            return "2인수의(공개견적)"
    if contract_method == "수의계약":
        return "1인수의(단일견적)"
    if contract_method == "입찰":
        return "자체(제한경쟁)"
    return ""


def full_address(value):
    text = re.sub(r"\s+", " ", str(value or "").strip())
    return "" if not text or text.lower() in ("nan", "none", "null") else text


def categorize_region_code(address, target_region):
    text = full_address(address)
    if target_region and target_region in text:
        return 1
    if "충남" in text or "충청남도" in text:
        return 2
    return 3


def region_label(code):
    return {1: "충남도내(관내)", 2: "충남도내(관외)", 3: "타시도"}.get(code, "타시도")


def classify_purchase_purpose(contract_name):
    text = re.sub(r"\s+", "", str(contract_name or ""))
    if not text:
        return "그 외"
    if "도서" in text and not any(
        key in text for key in ["교과용도서", "교과서", "업무용간행물", "신문"]
    ):
        return "도서(간행물 등)"
    if any(
        key in text
        for key in ["간식", "우유", "급식", "식재료", "식대", "도시락", "피복", "화초", "청소용", "시설관리"]
    ):
        return "그 외"
    education_keywords = [
        "학습준비물", "교재", "교구", "수업", "교육활동", "교육운영", "교육과정",
        "놀이자료", "미술재료", "특성화프로그램", "체험활동", "체험학습", "과학재료",
        "창의", "유아용", "교수학습", "특수학급", "방과후", "늘봄", "돌봄",
    ]
    return "교육용" if any(key in text for key in education_keywords) else "그 외"


def to_datetime_or_blank(value):
    if value in (None, "") or (isinstance(value, float) and pd.isna(value)):
        return ""
    try:
        return pd.to_datetime(value).to_pydatetime()
    except Exception:
        return str(value)


def format_money(value):
    try:
        return int(round(float(value)))
    except Exception:
        return 0


def propagate_known_addresses(df, headers):
    biz_col = source_col(headers, "biz")
    address_col = source_col(headers, "address")
    if biz_col is None or address_col is None:
        return 0

    biz_norm = df.iloc[:, biz_col].apply(normalize_biz_no)
    known = {}
    for idx in df.index:
        biz = biz_norm.at[idx]
        address = full_address(df.iat[idx, address_col])
        if biz and address and biz not in known:
            known[biz] = address

    filled = 0
    missing = missing_address_mask(df.iloc[:, address_col])
    for idx in df.index[missing]:
        address = known.get(biz_norm.at[idx], "")
        if address:
            df.iat[idx, address_col] = address
            filled += 1
    return filled


def apply_address_overrides(df, headers, business_addresses=None, row_addresses=None):
    business_addresses = business_addresses or {}
    row_addresses = row_addresses or {}
    biz_col = source_col(headers, "biz")
    address_col = source_col(headers, "address")
    if biz_col is None or address_col is None:
        raise ValueError("사업자등록번호 또는 주소 열을 찾지 못했습니다.")

    propagate_known_addresses(df, headers)
    biz_norm = df.iloc[:, biz_col].apply(normalize_biz_no)
    filled = 0

    for raw_biz, raw_address in business_addresses.items():
        biz = normalize_biz_no(raw_biz)
        address = full_address(raw_address)
        if not biz or not address:
            continue
        mask = biz_norm.eq(biz) & missing_address_mask(df.iloc[:, address_col])
        for idx in df.index[mask]:
            df.iat[idx, address_col] = address
            filled += 1

    for raw_idx, raw_address in row_addresses.items():
        try:
            idx = int(raw_idx)
        except (TypeError, ValueError):
            continue
        address = full_address(raw_address)
        if idx not in df.index or not address:
            continue
        if missing_address_mask(pd.Series([df.iat[idx, address_col]])).iloc[0]:
            df.iat[idx, address_col] = address
            filled += 1

    filled += propagate_known_addresses(df, headers)
    return filled


def records_from_source(df, headers, target_amount, target_region):
    cols = {key: find_source_col(headers, key) for key in HEADER_ALIASES}
    amount_col = source_col(headers, "amount")
    address_col = source_col(headers, "address")
    type_col = source_col(headers, "type")
    method_col = source_col(headers, "contract_method")
    competition_col = source_col(headers, "competition_method")

    amount = pd.to_numeric(df.iloc[:, amount_col], errors="coerce").fillna(0)
    work = df.loc[amount >= int(target_amount)]
    records = []

    for _, row in work.iterrows():
        ctype = normalize_contract_type(safe_value(row, type_col))
        if ctype not in ["공사", "용역", "물품"]:
            continue

        address = full_address(safe_value(row, address_col, ""))
        contract_name = str(safe_value(row, cols.get("contract_name"), "")).strip()
        contract_method = normalize_contract_method(safe_value(row, method_col, ""))
        competition = map_competition_method(
            safe_value(row, competition_col, ""), contract_method
        )

        records.append({
            "목적물": ctype,
            "계약방법": contract_method,
            "견적경쟁방법": competition,
            "계약명": contract_name,
            "계약일자": to_datetime_or_blank(safe_value(row, cols.get("contract_date"), "")),
            "계약금액": format_money(safe_value(row, amount_col, 0)),
            "업체명": str(safe_value(row, cols.get("company"), "")).strip(),
            "주소": address,
            "소재지": region_label(categorize_region_code(address, target_region)),
            "구입목적": classify_purchase_purpose(contract_name) if ctype == "물품" else "",
            "비고": "주소 미확인 → 타시도 임시분류" if not address else "",
        })

    return records


def _candidate_rows(df, missing_mask, biz_norm, company_col):
    rows = []
    seen_biz = set()
    for idx in df.index[missing_mask]:
        biz = str(biz_norm.at[idx] or "").strip()
        if biz and biz in seen_biz:
            continue
        if biz:
            seen_biz.add(biz)

        company = ""
        if company_col is not None and company_col < df.shape[1]:
            value = df.iat[idx, company_col]
            if pd.notna(value):
                company = str(value).strip()

        rows.append({
            "row_id": int(idx),
            "biz_no": biz,
            "company": company,
            "lookup_key": f"biz:{biz}" if biz else f"row:{idx}",
        })
    return rows


def inspect_workbooks(file_payloads, target_amount=DEFAULT_TARGET_AMOUNT, manual_region=""):
    df, headers = combine_workbooks(file_payloads)

    amount_col = find_source_col(headers, "amount")
    type_col = find_source_col(headers, "type")
    biz_col = find_source_col(headers, "biz")
    address_col = find_source_col(headers, "address")
    company_col = find_source_col(headers, "company")

    missing_columns = [
        name
        for name, idx in {
            "목적물": type_col,
            "계약금액": amount_col,
            "사업자등록번호": biz_col,
            "주소": address_col,
        }.items()
        if idx is None
    ]
    if missing_columns:
        raise ValueError("필수 열을 찾지 못했습니다: " + ", ".join(missing_columns))

    propagate_known_addresses(df, headers)

    amounts = pd.to_numeric(df.iloc[:, amount_col], errors="coerce").fillna(0)
    contract_types = df.iloc[:, type_col].apply(normalize_contract_type)
    recognized = contract_types.isin(["공사", "용역", "물품"])
    report_mask = (amounts >= int(target_amount)) & recognized

    biz_norm = df.iloc[:, biz_col].apply(normalize_biz_no)
    valid_biz = biz_norm.str.len().eq(10)
    missing = report_mask & missing_address_mask(df.iloc[:, address_col])

    auto_region, auto_region_count = _detect_region(df, address_col)
    target_region = manual_region if manual_region in CHUNGNAM_REGIONS else auto_region

    report_count = int(report_mask.sum())
    missing_count = int(missing.sum())
    completion = 0 if report_count == 0 else round((report_count - missing_count) / report_count * 100, 1)
    manual_candidates = _candidate_rows(df, missing, biz_norm, company_col)
    lookup_candidates = [row for row in manual_candidates if row["biz_no"]]

    institution, school_level = extract_source_metadata(df, headers)

    return {
        "file_count": len(file_payloads),
        "row_count": int(len(df)),
        "target_amount": int(target_amount),
        "auto_region": auto_region,
        "auto_region_evidence_count": int(auto_region_count),
        "target_region": target_region,
        "institution": institution,
        "school_level": school_level,
        "report_count": report_count,
        "missing_address_count": missing_count,
        "api_lookup_candidate_count": len(lookup_candidates),
        "api_lookup_candidate_row_count": int((missing & valid_biz).sum()),
        "address_completion_percent": completion,
        "lookup_candidates": lookup_candidates,
        "manual_candidates": manual_candidates,
    }
