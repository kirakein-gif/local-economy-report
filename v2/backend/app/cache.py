import os
import threading
import time

DEFAULT_POSITIVE_TTL = 7 * 86400
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
            "positive_ttl_seconds": DEFAULT_POSITIVE_TTL,
            "negative_ttl_seconds": DEFAULT_NEGATIVE_TTL,
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
                for old_key in expired:
                    self._local.pop(old_key, None)
                if len(self._local) >= MAX_LOCAL_ITEMS:
                    oldest = min(
                        self._local,
                        key=lambda k: int(self._local[k].get("updated_at", 0)),
                    )
                    self._local.pop(oldest, None)
            self._local[key] = dict(payload)

    def get(self, key):
        return self.get_many([key]).get(key)

    def get_many(self, keys):
        """Fetch cache entries with one Firestore get_all call for misses."""
        unique = []
        seen = set()
        for key in keys:
            key = str(key or "").strip()
            if key and key not in seen:
                seen.add(key)
                unique.append(key)

        results = {}
        firestore_keys = []
        for key in unique:
            local = self._local_get(key)
            if local is not None:
                local["cache_layer"] = "memory"
                results[key] = local
            else:
                firestore_keys.append(key)

        if self._firestore is None or not firestore_keys:
            return results

        try:
            collection = self._firestore.collection(self.collection_name)
            refs = [collection.document(key) for key in firestore_keys]
            now = int(time.time())
            for snapshot in self._firestore.get_all(refs):
                if not snapshot.exists:
                    continue
                data = snapshot.to_dict() or {}
                if int(data.get("expires_at", 0)) <= now:
                    continue
                key = snapshot.id
                self._local_set(key, data)
                item = dict(data)
                item["cache_layer"] = "firestore"
                results[key] = item
        except Exception as exc:
            self._firestore_error = str(exc)

        return results

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
