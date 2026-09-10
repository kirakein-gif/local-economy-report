import os
import re
import urllib.parse
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

from .cache import DEFAULT_NEGATIVE_TTL, DEFAULT_POSITIVE_TTL, address_cache
from .excel_service import normalize_biz_no
from .manual_store import get_manual_address

PROCUREMENT_URL = "https://apis.data.go.kr/1230000/ao/UsrInfoService02/getPrcrmntCorpBasicInfo02"
S2B_URL = "https://www.s2b.kr/S2BNCustomer/S2B/scrweb/common/search_api/search_json.jsp"
FTC_MAIL_ORDER_URL = "https://apis.data.go.kr/1130000/MllBsDtl_3Service/getMllBsInfoDetail_3"
LOCAL_FRANCHISE_URL = "https://apis.data.go.kr/B190001/localFranchisesV3/franchiseV3"

MAX_BULK_BUSINESSES = 200
DEFAULT_WORKERS = 2


def _clean(value):
    text = str(value or "").strip()
    return "" if text.lower() in ("", "n/a", "nan", "none", "null") else text


def _clean_s2b_address(value):
    text = _clean(value)
    return re.sub(r"^\(\s*\d{5}\s*\)\s*", "", text).strip()


def get_api_key():
    key = os.getenv("DATAGOKR", "") or os.getenv("datagokr", "")
    return str(key).strip()


def get_procurement_address(biz_num):
    biz = normalize_biz_no(biz_num)
    api_key = get_api_key()
    if not biz or not api_key:
        return None

    params = {
        "serviceKey": urllib.parse.unquote(api_key),
        "pageNo": "1",
        "numOfRows": "10",
        "type": "json",
        "inqryDiv": "3",
        "bizno": biz,
    }
    try:
        res = requests.get(PROCUREMENT_URL, params=params, timeout=10)
        res.raise_for_status()
        data = res.json()
        if "nkoneps.com.response.ResponseError" in data:
            return None

        items = data.get("response", {}).get("body", {}).get("items")
        if not items:
            return None

        item_list = items if isinstance(items, list) else items.get("item", [])
        if isinstance(item_list, dict):
            item_list = [item_list]

        for item in item_list or []:
            returned_biz = normalize_biz_no(
                item.get("bizno") or item.get("bizNo") or item.get("bizrno")
            )
            if returned_biz and returned_biz != biz:
                continue

            addr = " ".join(
                filter(None, [_clean(item.get("adrs")), _clean(item.get("dtlAdrs"))])
            ).strip()
            if addr:
                return addr
    except (requests.RequestException, ValueError, TypeError, KeyError):
        return None
    return None


def get_s2b_address(biz_num):
    biz = normalize_biz_no(biz_num)
    if not biz:
        return None

    payload = {
        "COMPANY_NAME": "",
        "CEO_NAME": "",
        "CITY_SEC": "",
        "GU": "",
        "SHOP_COMPANY": "",
        "ESTIMATE_COMPANY": "",
        "BUSINESS_NUMBER": biz,
        "CERT1": "",
        "CONDITIONS": "",
        "ITEMS": "",
        "CERT4": "",
        "AREA_BOOK_YN": "",
    }
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36"
        ),
        "Referer": "https://www.s2b.kr/",
    }

    try:
        res = requests.post(S2B_URL, data=payload, headers=headers, timeout=10)
        res.raise_for_status()
        data = res.json()

        collections = data.get("SearchQueryResult", {}).get("Collection", [])
        if isinstance(collections, dict):
            collections = [collections]

        for collection in collections or []:
            documents = collection.get("DocumentSet", {}).get("Document", [])
            if isinstance(documents, dict):
                documents = [documents]

            for document in documents or []:
                fields = document.get("Field", {})
                returned_biz = normalize_biz_no(
                    fields.get("BUSINESS_NUMBER") or fields.get("BIZ_NUMBER")
                )
                if returned_biz != biz:
                    continue

                addr = _clean_s2b_address(fields.get("ADDRESS"))
                if addr:
                    return addr
    except (requests.RequestException, ValueError, TypeError, KeyError):
        return None
    return None


def get_ftc_mail_order_address(biz_num):
    biz = normalize_biz_no(biz_num)
    api_key = get_api_key()
    if not biz or not api_key:
        return None

    params = {
        "serviceKey": urllib.parse.unquote(api_key),
        "pageNo": "1",
        "numOfRows": "10",
        "resultType": "xml",
        "brno": biz,
    }
    try:
        res = requests.get(FTC_MAIL_ORDER_URL, params=params, timeout=10)
        res.raise_for_status()
        root = ET.fromstring(res.content)

        if _clean(root.findtext("resultCode")) not in ("", "00"):
            return None

        for item in root.findall(".//item"):
            returned_biz = normalize_biz_no(item.findtext("brno"))
            if returned_biz != biz:
                continue

            addr = _clean(item.findtext("lctnAddr"))
            if not addr:
                addr = _clean(item.findtext("lctnRnAddr")) or _clean(item.findtext("rnAddr"))
            if addr:
                return addr
    except (requests.RequestException, ET.ParseError, TypeError, ValueError):
        return None
    return None


def get_local_franchise_address(biz_num):
    biz = normalize_biz_no(biz_num)
    api_key = get_api_key()
    if not biz or not api_key:
        return None

    params = {
        "serviceKey": urllib.parse.unquote(api_key),
        "page": "1",
        "perPage": "20",
        "cond[brno::EQ]": biz,
        "returnType": "JSON",
    }
    try:
        res = requests.get(LOCAL_FRANCHISE_URL, params=params, timeout=10)
        res.raise_for_status()
        data = res.json()

        rows = data.get("data", []) if isinstance(data, dict) else []
        if isinstance(rows, dict):
            rows = [rows]

        for item in rows or []:
            returned_biz = normalize_biz_no(item.get("brno"))
            if returned_biz != biz:
                continue

            base_addr = _clean(item.get("frcs_addr"))
            detail_addr = _clean(item.get("frcs_dtl_addr"))
            addr = " ".join(filter(None, [base_addr, detail_addr])).strip()
            if addr:
                return addr
    except (requests.RequestException, ValueError, TypeError, KeyError):
        return None
    return None


def _base_result(biz, **extra):
    result = {
        "biz_no": biz,
        "address": "",
        "source": "",
        "found": False,
        "cache_hit": False,
        "cache_layer": "",
        "cache_backend": address_cache.active_backend,
        "manual_hit": False,
        "invalid": False,
    }
    result.update(extra)
    return result


def lookup_address(biz_num, force_refresh=False):
    biz = normalize_biz_no(biz_num)
    if not biz:
        return _base_result("", invalid=True)

    manual = get_manual_address(biz)
    if manual:
        return _base_result(
            biz,
            address=manual.get("address", ""),
            source="사용자 저장주소",
            found=True,
            manual_hit=True,
            cache_layer=manual.get("backend", ""),
        )

    if not force_refresh:
        cached = address_cache.get(biz)
        if cached is not None:
            return _base_result(
                biz,
                address=cached.get("address", ""),
                source=cached.get("source", ""),
                found=bool(cached.get("found")),
                cache_hit=True,
                cache_layer=cached.get("cache_layer", ""),
            )

    sources = [
        ("나라장터", get_procurement_address),
        ("학교장터(S2B)", get_s2b_address),
        ("공정위 통신판매사업자", get_ftc_mail_order_address),
        ("지역화폐 가맹점", get_local_franchise_address),
    ]

    for source, getter in sources:
        address = getter(biz)
        if address:
            address_cache.set(
                biz,
                address=address,
                source=source,
                found=True,
                ttl_seconds=DEFAULT_POSITIVE_TTL,
            )
            return _base_result(
                biz,
                address=address,
                source=source,
                found=True,
            )

    address_cache.set(
        biz,
        address="",
        source="",
        found=False,
        ttl_seconds=DEFAULT_NEGATIVE_TTL,
    )
    return _base_result(biz)


def bulk_lookup_addresses(biz_numbers, force_refresh=False):
    normalized = []
    invalid = []
    seen = set()

    for value in biz_numbers:
        biz = normalize_biz_no(value)
        if not biz:
            invalid.append(str(value or ""))
            continue
        if biz in seen:
            continue
        seen.add(biz)
        normalized.append(biz)

    if len(normalized) > MAX_BULK_BUSINESSES:
        raise ValueError(
            f"한 번에 최대 {MAX_BULK_BUSINESSES}개 업체까지 주소를 조회할 수 있습니다."
        )

    worker_count = min(
        max(int(os.getenv("ADDRESS_LOOKUP_WORKERS", str(DEFAULT_WORKERS))), 1),
        4,
    )

    results_by_biz = {}
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = {
            executor.submit(lookup_address, biz, force_refresh): biz
            for biz in normalized
        }
        for future in as_completed(futures):
            biz = futures[future]
            try:
                results_by_biz[biz] = future.result()
            except Exception:
                results_by_biz[biz] = _base_result(biz)

    results = [results_by_biz[biz] for biz in normalized]
    source_counts = {
        "사용자 저장주소": 0,
        "나라장터": 0,
        "학교장터(S2B)": 0,
        "공정위 통신판매사업자": 0,
        "지역화폐 가맹점": 0,
    }
    for item in results:
        source = item.get("source")
        if item.get("found") and source in source_counts:
            source_counts[source] += 1

    return {
        "requested_count": len(biz_numbers),
        "unique_valid_count": len(normalized),
        "invalid_count": len(invalid),
        "found_count": sum(1 for item in results if item.get("found")),
        "not_found_count": sum(1 for item in results if not item.get("found")),
        "cache_hit_count": sum(1 for item in results if item.get("cache_hit")),
        "manual_hit_count": sum(1 for item in results if item.get("manual_hit")),
        "source_counts": source_counts,
        "cache": address_cache.status(),
        "results": results,
    }
