import re
import xml.etree.ElementTree as ET
import urllib.parse

import requests
import streamlit as st

from core_logic import get_api_key, normalize_biz_no

PROCUREMENT_URL = "https://apis.data.go.kr/1230000/ao/UsrInfoService02/getPrcrmntCorpBasicInfo02"
S2B_URL = "https://www.s2b.kr/S2BNCustomer/S2B/scrweb/common/search_api/search_json.jsp"
FTC_MAIL_ORDER_URL = "https://apis.data.go.kr/1130000/MllBsDtl_3Service/getMllBsInfoDetail_3"
LOCAL_FRANCHISE_URL = "https://apis.data.go.kr/B190001/localFranchisesV3/franchiseV3"


def _clean(value):
    text = str(value or "").strip()
    return "" if text.lower() in ("", "n/a", "nan", "none", "null") else text


def _clean_s2b_address(value):
    """S2B 주소 앞의 (우편번호) 표기를 제거합니다."""
    text = _clean(value)
    return re.sub(r"^\(\s*\d{5}\s*\)\s*", "", text).strip()


@st.cache_data(show_spinner=False, ttl=86400)
def get_procurement_address(biz_num):
    """나라장터에서 사업자번호가 정확히 일치하는 업체 주소를 조회합니다."""
    biz = normalize_biz_no(biz_num)
    if not biz:
        return None

    params = {
        "serviceKey": urllib.parse.unquote(get_api_key()),
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
            returned_biz = normalize_biz_no(item.get("bizno") or item.get("bizNo") or item.get("bizrno"))
            if returned_biz and returned_biz != biz:
                continue
            addr = " ".join(filter(None, [_clean(item.get("adrs")), _clean(item.get("dtlAdrs"))])).strip()
            if addr:
                return addr
    except (requests.RequestException, ValueError, TypeError, KeyError):
        return None
    return None


@st.cache_data(show_spinner=False, ttl=86400)
def get_s2b_address(biz_num):
    """학교장터(S2B) 공급업체 검색에서 사업자번호 정확일치로 주소를 조회합니다."""
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
                returned_biz = normalize_biz_no(fields.get("BUSINESS_NUMBER") or fields.get("BIZ_NUMBER"))
                if returned_biz != biz:
                    continue
                addr = _clean_s2b_address(fields.get("ADDRESS"))
                if addr:
                    return addr
    except (requests.RequestException, ValueError, TypeError, KeyError):
        return None
    return None


@st.cache_data(show_spinner=False, ttl=86400)
def get_ftc_mail_order_address(biz_num):
    """공정거래위원회 통신판매사업자 상세정보를 사업자번호로 조회합니다."""
    biz = normalize_biz_no(biz_num)
    if not biz:
        return None

    params = {
        "serviceKey": urllib.parse.unquote(get_api_key()),
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


@st.cache_data(show_spinner=False, ttl=86400)
def get_local_franchise_address(biz_num):
    """한국조폐공사 지역화폐 가맹점 V3에서 사업자번호 정확일치로 주소를 조회합니다."""
    biz = normalize_biz_no(biz_num)
    if not biz:
        return None

    params = {
        "serviceKey": urllib.parse.unquote(get_api_key()),
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


def get_address_from_public_apis(biz_num):
    """주소를 나라장터 → 학교장터(S2B) → 공정위 → 지역화폐 순으로 조회합니다.

    개별 조회 함수만 24시간 캐시하고 이 통합 함수는 캐시하지 않습니다.
    따라서 일시적인 전체 조회 실패(None, None)가 별도로 24시간 고정되지 않습니다.
    """
    biz = normalize_biz_no(biz_num)
    if not biz:
        return None, None

    addr = get_procurement_address(biz)
    if addr:
        return addr, "나라장터"

    addr = get_s2b_address(biz)
    if addr:
        return addr, "학교장터(S2B)"

    addr = get_ftc_mail_order_address(biz)
    if addr:
        return addr, "공정위 통신판매사업자"

    addr = get_local_franchise_address(biz)
    if addr:
        return addr, "지역화폐 가맹점"

    return None, None
