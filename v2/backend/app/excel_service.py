import re
from io import BytesIO

import pandas as pd

CHUNGNAM_REGIONS = [
    "천안", "아산", "공주", "보령", "서산", "논산", "계룡", "당진",
    "금산", "부여", "서천", "청양", "홍성", "예산", "태안",
]
DEFAULT_TARGET_AMOUNT = 500000

FALLBACK_COLS = {
    "type": 1,
    "contract_method": 2,
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
    "contract_name": ["계약명", "계약건명", "건명", "품명", "사업명"],
    "contract_date": ["계약일자", "계약일", "계약체결일", "계약일시"],
    "amount": ["계약금액(원)", "계약금액", "집행금액", "금액"],
    "company": ["업체명", "계약업체명", "계약상대자", "계약상대자명", "상호"],
    "biz": ["사업자등록번호", "사업자번호", "사업자 등록번호"],
    "address": ["주소", "업체주소", "사업장주소", "소재지주소"],
}


def normalize_header(value):
    return re.sub(r"[\s\n\r\t()（）\[\]{ }_/·ㆍ.-]+", "", str(value or "")).lower()


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


def _load_one(file_bytes):
    df = pd.read_excel(BytesIO(file_bytes))
    headers = [str(c).strip() for c in df.columns]
    df.columns = range(df.shape[1])
    if df.shape[1] < 21:
        df = df.reindex(columns=range(21))
        headers.extend([f"열{i + 1}" for i in range(len(headers), 21)])
    return df, headers


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


def inspect_workbooks(file_payloads, target_amount=DEFAULT_TARGET_AMOUNT, manual_region=""):
    loaded = [_load_one(payload) for payload in file_payloads]
    frames = [item[0] for item in loaded]
    headers = list(loaded[0][1])

    max_cols = max(frame.shape[1] for frame in frames)
    frames = [frame.reindex(columns=range(max_cols)) for frame in frames]
    if len(headers) < max_cols:
        headers.extend([f"열{i + 1}" for i in range(len(headers), max_cols)])

    df = pd.concat(frames, ignore_index=True)

    amount_col = find_source_col(headers, "amount")
    type_col = find_source_col(headers, "type")
    biz_col = find_source_col(headers, "biz")
    address_col = find_source_col(headers, "address")

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

    return {
        "file_count": len(file_payloads),
        "row_count": int(len(df)),
        "target_amount": int(target_amount),
        "auto_region": auto_region,
        "auto_region_evidence_count": int(auto_region_count),
        "target_region": target_region,
        "report_count": report_count,
        "missing_address_count": missing_count,
        "api_lookup_candidate_count": int((missing & valid_biz).sum()),
        "address_completion_percent": completion,
    }
