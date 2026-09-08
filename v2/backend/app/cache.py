import os
import threading
import time

DEFAULT_POSITIVE_TTL = 86400
DEFAULT_NEGATIVE_TTL = 900
MAX_LOCAL_ITEMS = 5000


class AddressCache:
    def __init__(self):
        self.requested_backend = os.getenv("ADDRESS_CACHE_BACKEND", "memory").strip().lower() or "memory"
        self.collection_name = os.getenv(
            "ADDRESS_CACHE_COLLECTION", "local_economy_address_cache"
        ).strip()
        self._local = {}
        self._lock = threading.RLock()
        self._firestore = None
        self._firestore_error = ""

        if self.requested_backend == "firestore":
            try:
                from google.cloud import firestore

                self._firestore = firestore.Client()
            except Exception as exc:
                self._firestore_error = str(exc)

    @property
    def active_backend(self):
        return "firestore" if self._firestore is not None else "memory"

    @property
    def firestore_error(self):
        return self._firestore_error

    def status(self):
        return {
            "requested": self.requested_backend,
            "active": self.active_backend,
            "collection": self.collection_name if self._firestore is not None else None,
            "fallback": self.requested_backend == "firestore" and self._firestore is None,
        }

    def _local_get(self, key):
        now = int(time.time())
        with self._lock:
            item = self._local.get(key)
            if not item:
                return None
            if int(item.get("expires_at", 0)) <= now:
                self._local.pop(key, None)
                return None
            return dict(item)

    def _local_set(self, key, payload):
        with self._lock:
            if len(self._local) >= MAX_LOCAL_ITEMS:
                expired = [
                    k
                    for k, v in self._local.items()
                    if int(v.get("expires_at", 0)) <= int(time.time())
                ]
                for old_key in expired[: max(1, len(expired))]:
                    self._local.pop(old_key, None)
                if len(self._local) >= MAX_LOCAL_ITEMS:
                    oldest = min(
                        self._local,
                        key=lambda k: int(self._local[k].get("updated_at", 0)),
                    )
                    self._local.pop(oldest, None)
            self._local[key] = dict(payload)

    def get(self, key):
        local = self._local_get(key)
        if local is not None:
            local["cache_layer"] = "memory"
            return local

        if self._firestore is None:
            return None

        try:
            snapshot = self._firestore.collection(self.collection_name).document(key).get()
            if not snapshot.exists:
                return None

            data = snapshot.to_dict() or {}
            if int(data.get("expires_at", 0)) <= int(time.time()):
                return None

            self._local_set(key, data)
            data["cache_layer"] = "firestore"
            return data
        except Exception as exc:
            self._firestore_error = str(exc)
            return None

    def set(self, key, *, address, source, found, ttl_seconds):
        now = int(time.time())
        payload = {
            "address": address or "",
            "source": source or "",
            "found": bool(found),
            "updated_at": now,
            "expires_at": now + int(ttl_seconds),
        }

        self._local_set(key, payload)

        if self._firestore is not None:
            try:
                self._firestore.collection(self.collection_name).document(key).set(payload)
            except Exception as exc:
                self._firestore_error = str(exc)

        return payload


address_cache = AddressCache()
