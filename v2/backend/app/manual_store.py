import os
import threading
from datetime import datetime, timezone

from .cache import address_cache
from .excel_service import normalize_biz_no

MANUAL_COLLECTION = os.getenv(
    "MANUAL_ADDRESS_COLLECTION", "local_economy_manual_addresses"
).strip()

_local_manual = {}
_local_lock = threading.RLock()


def _firestore_client():
    return getattr(address_cache, "_firestore", None)


def backend_name():
    return "firestore" if _firestore_client() is not None else "memory"


def get_manual_address(biz_num):
    biz = normalize_biz_no(biz_num)
    if not biz:
        return None

    client = _firestore_client()
    if client is not None:
        try:
            snap = client.collection(MANUAL_COLLECTION).document(biz).get()
            if snap.exists:
                data = snap.to_dict() or {}
                address = str(data.get("address", "")).strip()
                if address:
                    return {
                        "biz_no": biz,
                        "address": address,
                        "company_name": str(data.get("company_name", "")).strip(),
                        "updated_at": data.get("updated_at", ""),
                        "backend": "firestore",
                    }
        except Exception:
            pass

    with _local_lock:
        item = _local_manual.get(biz)
        return dict(item) if item else None


def get_manual_addresses(biz_numbers):
    results = {}
    for raw in biz_numbers:
        biz = normalize_biz_no(raw)
        if not biz or biz in results:
            continue
        item = get_manual_address(biz)
        if item:
            results[biz] = item
    return results


def save_manual_address(biz_num, address, company_name=""):
    biz = normalize_biz_no(biz_num)
    address = str(address or "").strip()
    company_name = str(company_name or "").strip()
    if not biz:
        raise ValueError("10자리 사업자등록번호가 필요합니다.")
    if not address:
        raise ValueError("저장할 주소를 입력해 주세요.")

    payload = {
        "biz_no": biz,
        "address": address,
        "company_name": company_name,
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }

    client = _firestore_client()
    if client is not None:
        try:
            client.collection(MANUAL_COLLECTION).document(biz).set(payload)
            payload["backend"] = "firestore"
            return payload
        except Exception:
            pass

    with _local_lock:
        _local_manual[biz] = dict(payload, backend="memory")
    return dict(payload, backend="memory")
