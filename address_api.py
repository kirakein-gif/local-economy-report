import xml.etree.ElementTree as ET
import urllib.parse

import requests
import streamlit as st

from core_logic import get_api_key, normalize_biz_no

PROCUREMENT_URL = "https://apis.data.go.kr/1230000/ao/UsrInfoService02/getPrcrmntCorpBasicInfo02"
FTC_MAIL_ORDER_URL = "https://apis.data.go.kr/1130000/MllBsDtl_3Service/getMllBsInfoDetail_3"
LOCAL_FRANCHISE_URL = "https://apis.data.go.kr/B190001/localFranchisesV2/franchiseV2"


def _clean(value):
    text = str(value or "").strip()
    return "" if text.lower() in ("", "n/a", "nan", "none", "null") else text


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
    """전국 지역화폐 가맹점 정보에서 사업자번호 정확일치로 주소를 조회합니다."""
    biz = normalize_biz_no(biz_num)
    if not biz:
        return None

    params = {
        "serviceKey": urllib.parse.unquote(get_api_key()),
        "page": "1",
        "perPage": "20",
        "returnType": "JSON",
        "cond[brno::EQ]": biz,
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


@st.cache_data(show_spinner=False, ttl=86400)
def get_address_from_public_apis(biz_num):
    """주소를 나라장터 → 공정위 통신판매사업자 → 지역화폐 가맹점 순으로 조회합니다."""
    biz = normalize_biz_no(biz_num)
    if not biz:
        return None, None

    addr = get_procurement_address(biz)
    if addr:
        return addr, "나라장터"

    addr = get_ftc_mail_order_address(biz)
    if addr:
        return addr, "공정위 통신판매사업자"

    addr = get_local_franchise_address(biz)
    if addr:
        return addr, "지역화폐 가맹점"

    return None, None
