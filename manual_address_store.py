import base64
import json
import time
from datetime import datetime, timezone

import requests
import streamlit as st

from core_logic import normalize_biz_no

REPO = "kirakein-gif/local-economy-report"
BRANCH = "main"
STORE_PATH = "data/manual_addresses.json"
API_URL = f"https://api.github.com/repos/{REPO}/contents/{STORE_PATH}"


def _token():
    """Streamlit Secrets의 GitHub 쓰기 토큰을 가져옵니다."""
    try:
        return str(st.secrets.get("GITHUB_TOKEN", "")).strip()
    except Exception:
        return ""


def _headers(write=False):
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "local-economy-report",
    }
    token = _token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _decode_contents_payload(payload):
    raw = base64.b64decode(payload.get("content", "")).decode("utf-8")
    data = json.loads(raw) if raw.strip() else {}
    return data if isinstance(data, dict) else {}


def load_manual_addresses():
    """GitHub Contents API에서 공유 수동주소의 최신본을 직접 읽습니다."""
    try:
        res = requests.get(
            API_URL,
            params={"ref": BRANCH, "t": int(time.time() * 1000)},
            headers=_headers(),
            timeout=8,
        )
        res.raise_for_status()
        return _decode_contents_payload(res.json())
    except (requests.RequestException, ValueError, TypeError, KeyError, json.JSONDecodeError):
        return {}


def get_manual_address(biz_num, store=None):
    biz = normalize_biz_no(biz_num)
    if not biz:
        return None
    data = store if isinstance(store, dict) else load_manual_addresses()
    item = data.get(biz)
    if isinstance(item, str):
        return item.strip() or None
    if isinstance(item, dict):
        return str(item.get("address", "")).strip() or None
    return None


def _read_for_update():
    """GitHub 최신 파일과 SHA를 읽습니다."""
    res = requests.get(API_URL, params={"ref": BRANCH}, headers=_headers(), timeout=8)
    res.raise_for_status()
    payload = res.json()
    data = _decode_contents_payload(payload)
    return data, payload["sha"]


def save_manual_address(biz_num, address, company_name=""):
    """사업자번호별 수동주소를 공유 JSON에 저장합니다. 충돌 시 최신본을 다시 읽어 재시도합니다."""
    biz = normalize_biz_no(biz_num)
    address = str(address or "").strip()
    company_name = str(company_name or "").strip()
    if not biz or not address:
        return False, "사업자번호 또는 주소가 올바르지 않습니다."
    if not _token():
        return False, "공유주소 저장용 GITHUB_TOKEN이 설정되지 않았습니다."

    for attempt in range(3):
        try:
            data, sha = _read_for_update()
            old = data.get(biz, {})
            old_address = old.get("address", "") if isinstance(old, dict) else str(old or "")
            now = datetime.now(timezone.utc).isoformat(timespec="seconds")
            data[biz] = {
                "address": address,
                "company_name": company_name,
                "status": "manual",
                "updated_at": now,
                "previous_address": old_address if old_address and old_address != address else "",
            }
            encoded = base64.b64encode(
                (json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
            ).decode("ascii")
            body = {
                "message": f"Update shared address for {biz}",
                "content": encoded,
                "sha": sha,
                "branch": BRANCH,
            }
            res = requests.put(API_URL, headers=_headers(write=True), json=body, timeout=10)
            if res.status_code in (200, 201):
                return True, "공유주소에 저장했습니다."
            if res.status_code in (409, 422) and attempt < 2:
                time.sleep(0.25 * (attempt + 1))
                continue
            return False, f"공유주소 저장 실패({res.status_code})"
        except (requests.RequestException, ValueError, TypeError, KeyError, json.JSONDecodeError):
            if attempt < 2:
                time.sleep(0.25 * (attempt + 1))
                continue
            return False, "공유주소 저장 중 오류가 발생했습니다."

    return False, "공유주소 저장에 실패했습니다."
