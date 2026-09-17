import base64
import json
import os
import threading
import time
from datetime import datetime, timezone

import requests

from .manual_store import MANUAL_COLLECTION, backend_name, export_manual_addresses

BACKUP_REPO = os.getenv(
    "MANUAL_BACKUP_REPO", "kirakein-gif/local-economy-report"
).strip()
BACKUP_BRANCH = os.getenv("MANUAL_BACKUP_BRANCH", "address-backups").strip()
BACKUP_PATH = os.getenv(
    "MANUAL_BACKUP_PATH", "backup/firestore_manual_addresses.json"
).strip()
BACKUP_INTERVAL_SECONDS = max(
    int(os.getenv("MANUAL_BACKUP_INTERVAL_SECONDS", "86400")),
    3600,
)

_backup_lock = threading.Lock()
_last_attempt_monotonic = 0.0
_last_status = {
    "configured": False,
    "status": "not_configured",
    "record_count": 0,
    "last_attempt_at": "",
    "last_commit_at": "",
    "error": "",
}


def _token():
    return str(os.getenv("GITHUB_BACKUP_TOKEN", "") or "").strip()


def backup_configured():
    return bool(_token() and BACKUP_REPO and BACKUP_BRANCH and BACKUP_PATH)


def backup_status():
    with _backup_lock:
        status = dict(_last_status)
    status["configured"] = backup_configured()
    status["branch"] = BACKUP_BRANCH
    status["path"] = BACKUP_PATH
    return status


def _headers():
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {_token()}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "local-economy-report-v2-backup",
    }


def _api_url():
    return f"https://api.github.com/repos/{BACKUP_REPO}/contents/{BACKUP_PATH}"


def _stable_backup_text():
    addresses = export_manual_addresses()
    payload = {
        "schema_version": 1,
        "source": {
            "type": "firestore",
            "collection": MANUAL_COLLECTION,
        },
        "addresses": addresses,
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    return text, len(addresses)


def _read_existing():
    response = requests.get(
        _api_url(),
        params={"ref": BACKUP_BRANCH},
        headers=_headers(),
        timeout=10,
    )
    if response.status_code == 404:
        return "", ""
    response.raise_for_status()
    payload = response.json()
    current = base64.b64decode(payload.get("content", "")).decode("utf-8")
    return current, str(payload.get("sha", "") or "")


def _write_backup(content, sha=""):
    body = {
        "message": f"Backup Firestore manual addresses {datetime.now(timezone.utc).date().isoformat()}",
        "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
        "branch": BACKUP_BRANCH,
    }
    if sha:
        body["sha"] = sha
    response = requests.put(
        _api_url(),
        headers=_headers(),
        json=body,
        timeout=12,
    )
    response.raise_for_status()
    return response.json()


def backup_manual_addresses(force=False):
    """Back up Firestore manual addresses to a dedicated GitHub branch.

    The snapshot is deterministic. A GitHub commit is created only when the
    address data actually changes. Backup failure never mutates Firestore.
    """
    global _last_attempt_monotonic

    now_monotonic = time.monotonic()
    now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")

    with _backup_lock:
        if not force and _last_attempt_monotonic:
            if now_monotonic - _last_attempt_monotonic < BACKUP_INTERVAL_SECONDS:
                return dict(_last_status)
        _last_attempt_monotonic = now_monotonic

    if not backup_configured():
        result = {
            "configured": False,
            "status": "not_configured",
            "record_count": 0,
            "last_attempt_at": now_iso,
            "last_commit_at": _last_status.get("last_commit_at", ""),
            "error": "GITHUB_BACKUP_TOKEN이 설정되지 않았습니다.",
        }
        with _backup_lock:
            _last_status.update(result)
            return dict(_last_status)

    if backend_name() != "firestore":
        result = {
            "configured": True,
            "status": "skipped_no_firestore",
            "record_count": 0,
            "last_attempt_at": now_iso,
            "last_commit_at": _last_status.get("last_commit_at", ""),
            "error": "Firestore가 활성화되지 않았습니다.",
        }
        with _backup_lock:
            _last_status.update(result)
            return dict(_last_status)

    try:
        desired, record_count = _stable_backup_text()

        for attempt in range(2):
            current, sha = _read_existing()
            if current == desired:
                result = {
                    "configured": True,
                    "status": "no_change",
                    "record_count": record_count,
                    "last_attempt_at": now_iso,
                    "last_commit_at": _last_status.get("last_commit_at", ""),
                    "error": "",
                }
                break

            try:
                _write_backup(desired, sha=sha)
                result = {
                    "configured": True,
                    "status": "committed",
                    "record_count": record_count,
                    "last_attempt_at": now_iso,
                    "last_commit_at": now_iso,
                    "error": "",
                }
                break
            except requests.HTTPError as exc:
                status_code = getattr(exc.response, "status_code", None)
                if status_code in (409, 422) and attempt == 0:
                    time.sleep(0.3)
                    continue
                raise
        else:
            raise RuntimeError("GitHub 백업 충돌 재시도에 실패했습니다.")
    except Exception as exc:
        result = {
            "configured": True,
            "status": "error",
            "record_count": 0,
            "last_attempt_at": now_iso,
            "last_commit_at": _last_status.get("last_commit_at", ""),
            "error": str(exc),
        }

    with _backup_lock:
        _last_status.update(result)
        return dict(_last_status)
