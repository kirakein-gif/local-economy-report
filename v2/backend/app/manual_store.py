import os
import threading
from datetime import datetime, timezone

import requests
from google.api_core.exceptions import AlreadyExists

from .cache import address_cache
from .excel_service import normalize_biz_no

MANUAL_COLLECTION = os.getenv(
    "MANUAL_ADDRESS_COLLECTION", "local_economy_manual_addresses"
).strip()
LEGACY_MANUAL_URL = os.getenv(
    "LEGACY_MANUAL_ADDRESS_URL",
    "https://raw.githubusercontent.com/kirakein-gif/local-economy-report/main/data/manual_addresses.json",
).strip()
LEGACY_MIGRATION_ENABLED = os.getenv("LEGACY_MANUAL_MIGRATION_ENABLED", "1").strip().lower() not in {
    "0",
    "false",
    "no",
    "off",
}

_local_manual = {}
_local_lock = threading.RLock()
_migration_lock = threading.Lock()
_migration_status = {
    "attempted": False,
    "source": "github_legacy",
    "loaded_count": 0,
    "created_count": 0,
    "existing_count": 0,
    "invalid_count": 0,
    "error_count": 0,
    "error": "",
}


def _firestore_client():
    return getattr(address_cache, "_firestore", None)


def backend_name():
    return "firestore" if _firestore_client() is not None else "memory"


def migration_status():
    with _migration_lock:
        return dict(_migration_status)


def _clean_manual_record(biz_num, item):
    biz = normalize_biz_no(biz_num)
    if not biz:
        return None

    if isinstance(item, str):
        address = item.strip()
        company_name = ""
        updated_at = ""
        previous_address = ""
    elif isinstance(item, dict):
        address = str(item.get("address", "") or "").strip()
        company_name = str(item.get("company_name", "") or "").strip()
        updated_at = str(item.get("updated_at", "") or "").strip()
        previous_address = str(item.get("previous_address", "") or "").strip()
    else:
        return None

    if not address:
        return None

    return {
        "biz_no": biz,
        "address": address,
        "company_name": company_name,
        "status": "manual",
        "source": "manual",
        "updated_at": updated_at or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "previous_address": previous_address,
    }


def _load_legacy_manual_addresses():
    if not LEGACY_MIGRATION_ENABLED or not LEGACY_MANUAL_URL:
        return {}

    response = requests.get(
        LEGACY_MANUAL_URL,
        headers={"User-Agent": "local-economy-report-v2-migration"},
        timeout=8,
    )
    response.raise_for_status()
    payload = response.json()
    return payload if isinstance(payload, dict) else {}


def migrate_legacy_manual_addresses():
    """Import the legacy GitHub manual-address store without overwriting Firestore.

    Firestore DocumentReference.create() is intentionally used instead of set().
    If a business number already exists, the existing Firestore value wins.
    This keeps the migration idempotent and safe when multiple Cloud Run
    instances start at the same time.
    """
    client = _firestore_client()
    with _migration_lock:
        if _migration_status["attempted"]:
            return dict(_migration_status)
        _migration_status["attempted"] = True

    if client is None:
        with _migration_lock:
            _migration_status["error"] = "Firestore가 활성화되지 않아 이관을 건너뜁니다."
            return dict(_migration_status)

    try:
        legacy = _load_legacy_manual_addresses()
    except Exception as exc:
        with _migration_lock:
            _migration_status["error"] = str(exc)
            return dict(_migration_status)

    result = {
        "attempted": True,
        "source": "github_legacy",
        "loaded_count": len(legacy),
        "created_count": 0,
        "existing_count": 0,
        "invalid_count": 0,
        "error_count": 0,
        "error": "",
    }
    migrated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    collection = client.collection(MANUAL_COLLECTION)

    for raw_biz, raw_item in legacy.items():
        payload = _clean_manual_record(raw_biz, raw_item)
        if not payload:
            result["invalid_count"] += 1
            continue

        payload["migrated_from"] = "github_legacy"
        payload["migrated_at"] = migrated_at
        try:
            collection.document(payload["biz_no"]).create(payload)
            result["created_count"] += 1
        except AlreadyExists:
            result["existing_count"] += 1
        except Exception:
            result["error_count"] += 1

    with _migration_lock:
        _migration_status.update(result)
        return dict(_migration_status)


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
                        "source": str(data.get("source", "manual") or "manual"),
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


def export_manual_addresses():
    """Return a deterministic snapshot of user-entered addresses for backup."""
    client = _firestore_client()
    exported = {}

    if client is not None:
        try:
            for snap in client.collection(MANUAL_COLLECTION).stream():
                data = snap.to_dict() or {}
                payload = _clean_manual_record(snap.id, data)
                if not payload:
                    continue
                record = {
                    "address": payload["address"],
                    "company_name": payload["company_name"],
                    "status": "manual",
                    "updated_at": payload["updated_at"],
                }
                previous_address = str(data.get("previous_address", "") or "").strip()
                if previous_address:
                    record["previous_address"] = previous_address
                migrated_from = str(data.get("migrated_from", "") or "").strip()
                if migrated_from:
                    record["migrated_from"] = migrated_from
                exported[payload["biz_no"]] = record
            return dict(sorted(exported.items()))
        except Exception:
            pass

    with _local_lock:
        for biz, data in _local_manual.items():
            payload = _clean_manual_record(biz, data)
            if payload:
                exported[biz] = {
                    "address": payload["address"],
                    "company_name": payload["company_name"],
                    "status": "manual",
                    "updated_at": payload["updated_at"],
                }
    return dict(sorted(exported.items()))


def save_manual_address(biz_num, address, company_name=""):
    biz = normalize_biz_no(biz_num)
    address = str(address or "").strip()
    company_name = str(company_name or "").strip()
    if not biz:
        raise ValueError("10자리 사업자등록번호가 필요합니다.")
    if not address:
        raise ValueError("저장할 주소를 입력해 주세요.")

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    payload = {
        "biz_no": biz,
        "address": address,
        "company_name": company_name,
        "status": "manual",
        "source": "manual",
        "updated_at": now,
    }

    client = _firestore_client()
    if client is not None:
        try:
            document = client.collection(MANUAL_COLLECTION).document(biz)
            old = document.get()
            if old.exists:
                old_data = old.to_dict() or {}
                old_address = str(old_data.get("address", "") or "").strip()
                if old_address and old_address != address:
                    payload["previous_address"] = old_address
            document.set(payload, merge=True)
            return dict(payload, backend="firestore")
        except Exception:
            pass

    with _local_lock:
        old = _local_manual.get(biz, {})
        old_address = str(old.get("address", "") or "").strip()
        if old_address and old_address != address:
            payload["previous_address"] = old_address
        _local_manual[biz] = dict(payload, backend="memory")
    return dict(payload, backend="memory")
