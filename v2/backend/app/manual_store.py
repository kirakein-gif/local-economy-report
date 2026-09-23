import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path

from google.api_core.exceptions import AlreadyExists

from .cache import address_cache
from .excel_service import normalize_biz_no

MANUAL_COLLECTION = os.getenv(
    "MANUAL_ADDRESS_COLLECTION", "local_economy_manual_addresses"
).strip()
SYSTEM_COLLECTION = os.getenv(
    "SYSTEM_COLLECTION", "local_economy_system"
).strip()
MIGRATION_DOC_ID = "manual_addresses_migration_v1"
LEGACY_MANUAL_FILE = os.getenv(
    "LEGACY_MANUAL_ADDRESS_FILE", "/app/data/manual_addresses.json"
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
    "source": "bundled_legacy_snapshot",
    "loaded_count": 0,
    "created_count": 0,
    "existing_count": 0,
    "invalid_count": 0,
    "error_count": 0,
    "completed": False,
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


def _snapshot_to_manual(snapshot):
    if not snapshot or not snapshot.exists:
        return None
    data = snapshot.to_dict() or {}
    address = str(data.get("address", "") or "").strip()
    if not address:
        return None
    return {
        "biz_no": snapshot.id,
        "address": address,
        "company_name": str(data.get("company_name", "") or "").strip(),
        "updated_at": data.get("updated_at", ""),
        "source": str(data.get("source", "manual") or "manual"),
        "backend": "firestore",
    }


def _load_legacy_manual_addresses():
    if not LEGACY_MIGRATION_ENABLED or not LEGACY_MANUAL_FILE:
        return {}

    path = Path(LEGACY_MANUAL_FILE)
    if not path.exists():
        return {}

    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def migrate_legacy_manual_addresses():
    """Import the bundled legacy snapshot once without overwriting Firestore.

    A Firestore marker avoids re-scanning every legacy address on future cold starts.
    DocumentReference.create() guarantees that an existing Firestore address always wins.
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

    marker_ref = client.collection(SYSTEM_COLLECTION).document(MIGRATION_DOC_ID)
    try:
        marker = marker_ref.get()
        if marker.exists and bool((marker.to_dict() or {}).get("completed")):
            marker_data = marker.to_dict() or {}
            with _migration_lock:
                _migration_status.update({
                    "completed": True,
                    "loaded_count": int(marker_data.get("loaded_count", 0) or 0),
                    "created_count": int(marker_data.get("created_count", 0) or 0),
                    "existing_count": int(marker_data.get("existing_count", 0) or 0),
                    "error": "",
                })
                return dict(_migration_status)
    except Exception as exc:
        with _migration_lock:
            _migration_status["error"] = f"이관 상태 확인 실패: {exc}"

    try:
        legacy = _load_legacy_manual_addresses()
    except Exception as exc:
        with _migration_lock:
            _migration_status["error"] = str(exc)
            return dict(_migration_status)

    result = {
        "attempted": True,
        "source": "bundled_legacy_snapshot",
        "loaded_count": len(legacy),
        "created_count": 0,
        "existing_count": 0,
        "invalid_count": 0,
        "error_count": 0,
        "completed": False,
        "error": "",
    }
    migrated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    collection = client.collection(MANUAL_COLLECTION)

    for raw_biz, raw_item in legacy.items():
        payload = _clean_manual_record(raw_biz, raw_item)
        if not payload:
            result["invalid_count"] += 1
            continue

        payload["migrated_from"] = "github_legacy_snapshot"
        payload["migrated_at"] = migrated_at
        try:
            collection.document(payload["biz_no"]).create(payload)
            result["created_count"] += 1
        except AlreadyExists:
            result["existing_count"] += 1
        except Exception:
            result["error_count"] += 1

    if result["error_count"] == 0:
        result["completed"] = True
        try:
            marker_ref.set({
                "completed": True,
                "completed_at": migrated_at,
                "loaded_count": result["loaded_count"],
                "created_count": result["created_count"],
                "existing_count": result["existing_count"],
            })
        except Exception as exc:
            result["completed"] = False
            result["error"] = f"이관 완료표시 저장 실패: {exc}"

    with _migration_lock:
        _migration_status.update(result)
        return dict(_migration_status)


def get_manual_address(biz_num):
    biz = normalize_biz_no(biz_num)
    if not biz:
        return None
    return get_manual_addresses([biz]).get(biz)


def get_manual_addresses(biz_numbers):
    unique = []
    seen = set()
    for raw in biz_numbers:
        biz = normalize_biz_no(raw)
        if biz and biz not in seen:
            seen.add(biz)
            unique.append(biz)

    results = {}
    client = _firestore_client()
    if client is not None and unique:
        try:
            collection = client.collection(MANUAL_COLLECTION)
            refs = [collection.document(biz) for biz in unique]
            for snapshot in client.get_all(refs):
                item = _snapshot_to_manual(snapshot)
                if item:
                    results[item["biz_no"]] = item
        except Exception:
            pass

    with _local_lock:
        for biz in unique:
            if biz in results:
                continue
            item = _local_manual.get(biz)
            if item:
                results[biz] = dict(item)

    return results


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
