import os
import re
import threading
import time
import urllib.parse
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

from .cache import DEFAULT_NEGATIVE_TTL, DEFAULT_POSITIVE_TTL, address_cache
from .excel_service import normalize_biz_no
from .manual_store import get_manual_address, get_manual_addresses

PROCUREMENT_URL = "https://apis.data.go.kr/1230000/ao/UsrInfoService02/getPrcrmntCorpBasicInfo02"
S2B_URL = "https://www.s2b.kr/S2BNCustomer/S2B/scrweb/common/search_api/search_json.jsp"
FTC_MAIL_ORDER_URL = "https://apis.data.go.kr/1130000/MllBsDtl_3Service/getMllBsInfoDetail_3"
LOCAL_FRANCHISE_URL = "https://apis.data.go.kr/B190001/localFranchisesV3/franchiseV3"

MAX_BULK_BUSINESSES = 200
DEFAULT_WORKERS = 2
API_TIMEOUT = (3.05, 8)
_http_local = threading.local()

PUBLIC_SOURCE_NAMES = {
    "나라장터",
    "학교장터(S2B)",
    "공정위 통신판매사업자",
    "지역화폐 가맹점",
}


def _http_session():
    session = getattr(_http_local, "session", None)
    if session is None:
        session = requests.Session()
        _http_local.session = session
    return session


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
        res = _http_session().get(PROCUREMENT_URL, params=params, timeout=API_TIMEOUT)
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
        res = _http_session().post(S2B_URL, data=payload, headers=headers, timeout=API_TIMEOUT)
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
        res = _http_session().get(FTC_MAIL_ORDER_URL, params=params, timeout=API_TIMEOUT)
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
        res = _http_session().get(LOCAL_FRANCHISE_URL, params=params, timeout=API_TIMEOUT)
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
        "verified_at": 0,
        "stale": False,
        "manual_hit": False,
        "manual_suggestion": False,
        "saved_address": "",
        "saved_company_name": "",
        "invalid": False,
    }
    result.update(extra)
    return result


def _emit(progress_callback, event):
    if progress_callback is None:
        return
    try:
        progress_callback(dict(event))
    except Exception:
        pass


def _manual_suggestion(biz, manual=None, *, cache_hit=False, cache_layer=""):
    manual = manual if manual is not None else get_manual_address(biz)
    if not manual:
        return _base_result(
            biz,
            cache_hit=cache_hit,
            cache_layer=cache_layer,
        )
    return _base_result(
        biz,
        cache_hit=cache_hit,
        cache_layer=cache_layer,
        manual_suggestion=True,
        saved_address=manual.get("address", ""),
        saved_company_name=manual.get("company_name", ""),
    )


def _lookup_public_sources(
    biz,
    manual=None,
    progress_callback=None,
    preferred_source="",
    previous_cache=None,
):
    sources = [
        ("나라장터", get_procurement_address),
        ("학교장터(S2B)", get_s2b_address),
        ("공정위 통신판매사업자", get_ftc_mail_order_address),
        ("지역화폐 가맹점", get_local_franchise_address),
    ]
    if preferred_source:
        sources.sort(key=lambda item: 0 if item[0] == preferred_source else 1)

    for source, getter in sources:
        _emit(progress_callback, {
            "type": "source",
            "biz_no": biz,
            "source": source,
        })
        address = getter(biz)
        if address:
            address_cache.set(
                biz,
                address=address,
                source=source,
                found=True,
                ttl_seconds=DEFAULT_POSITIVE_TTL,
                previous_item=previous_cache,
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
        previous_item=previous_cache,
    )
    return _manual_suggestion(biz, manual=manual)


def lookup_address(biz_num, force_refresh=False, progress_callback=None):
    biz = normalize_biz_no(biz_num)
    if not biz:
        return _base_result("", invalid=True)

    cached = address_cache.get(biz, include_expired=True)
    if cached is not None and not force_refresh and not cached.get("stale"):
        cached_source = str(cached.get("source", "") or "")
        cached_found = bool(cached.get("found"))
        cache_layer = cached.get("cache_layer", "")

        if cached_found and cached_source in PUBLIC_SOURCE_NAMES:
            return _base_result(
                biz,
                address=cached.get("address", ""),
                source=cached_source,
                found=True,
                cache_hit=True,
                cache_layer=cache_layer,
                verified_at=int(cached.get("verified_at", cached.get("updated_at", 0)) or 0),
            )

        if not cached_found:
            return _manual_suggestion(
                biz,
                cache_hit=True,
                cache_layer=cache_layer,
            )

    preferred_source = ""
    if cached and bool(cached.get("found")):
        candidate_source = str(cached.get("source", "") or "")
        if candidate_source in PUBLIC_SOURCE_NAMES:
            preferred_source = candidate_source

    return _lookup_public_sources(
        biz,
        manual=get_manual_address(biz),
        progress_callback=progress_callback,
        preferred_source=preferred_source,
        previous_cache=cached,
    )


def bulk_lookup_addresses(biz_numbers, force_refresh=False, progress_callback=None):
    started = time.perf_counter()
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

    total = len(normalized)
    _emit(progress_callback, {
        "type": "start",
        "total": total,
        "requested_count": len(biz_numbers),
    })

    # One batch read for trusted API cache and one batch read for user-saved suggestions.
    cached_by_biz = address_cache.get_many(normalized, include_expired=True)
    manual_by_biz = get_manual_addresses(normalized)

    results_by_biz = {}
    pending = {}
    completed = 0

    def complete(biz, item):
        nonlocal completed
        results_by_biz[biz] = item
        completed += 1
        _emit(progress_callback, {
            "type": "complete",
            "biz_no": biz,
            "completed": completed,
            "total": total,
            "found": bool(item.get("found")),
            "source": item.get("source", ""),
            "cache_hit": bool(item.get("cache_hit")),
            "manual_suggestion": bool(item.get("manual_suggestion")),
        })

    for biz in normalized:
        cached = cached_by_biz.get(biz)
        if cached is None:
            pending[biz] = None
            continue

        cached_source = str(cached.get("source", "") or "")
        cache_layer = cached.get("cache_layer", "")
        if (
            not force_refresh
            and not cached.get("stale")
            and bool(cached.get("found"))
            and cached_source in PUBLIC_SOURCE_NAMES
        ):
            complete(
                biz,
                _base_result(
                    biz,
                    address=cached.get("address", ""),
                    source=cached_source,
                    found=True,
                    cache_hit=True,
                    cache_layer=cache_layer,
                    verified_at=int(cached.get("verified_at", cached.get("updated_at", 0)) or 0),
                ),
            )
        elif not force_refresh and not cached.get("stale") and not bool(cached.get("found")):
            complete(
                biz,
                _manual_suggestion(
                    biz,
                    manual=manual_by_biz.get(biz),
                    cache_hit=True,
                    cache_layer=cache_layer,
                ),
            )
        else:
            pending[biz] = cached

    worker_count = min(
        max(int(os.getenv("ADDRESS_LOOKUP_WORKERS", str(DEFAULT_WORKERS))), 1),
        4,
    )

    if pending:
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            futures = {
                executor.submit(
                    _lookup_public_sources,
                    biz,
                    manual_by_biz.get(biz),
                    progress_callback,
                    (
                        str(previous.get("source", "") or "")
                        if previous and bool(previous.get("found"))
                        and str(previous.get("source", "") or "") in PUBLIC_SOURCE_NAMES
                        else ""
                    ),
                    previous,
                ): biz
                for biz, previous in pending.items()
            }
            for future in as_completed(futures):
                biz = futures[future]
                try:
                    item = future.result()
                except Exception:
                    item = _manual_suggestion(biz, manual=manual_by_biz.get(biz))
                complete(biz, item)

    results = [results_by_biz[biz] for biz in normalized]
    source_counts = {
        "나라장터": 0,
        "학교장터(S2B)": 0,
        "공정위 통신판매사업자": 0,
        "지역화폐 가맹점": 0,
    }
    for item in results:
        source = item.get("source")
        if item.get("found") and source in source_counts:
            source_counts[source] += 1

    result = {
        "requested_count": len(biz_numbers),
        "unique_valid_count": len(normalized),
        "invalid_count": len(invalid),
        "found_count": sum(1 for item in results if item.get("found")),
        "not_found_count": sum(1 for item in results if not item.get("found")),
        "cache_hit_count": sum(
            1 for item in results if item.get("cache_hit") and item.get("found")
        ),
        "negative_cache_hit_count": sum(
            1 for item in results if item.get("cache_hit") and not item.get("found")
        ),
        "manual_hit_count": 0,
        "manual_suggestion_count": sum(
            1 for item in results if item.get("manual_suggestion")
        ),
        "source_counts": source_counts,
        "cache": address_cache.status(),
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 1),
        "results": results,
    }
    return result
