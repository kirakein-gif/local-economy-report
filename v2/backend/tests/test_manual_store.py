import unittest
from unittest.mock import patch

from google.api_core.exceptions import AlreadyExists

from app import manual_store


class FakeSnapshot:
    def __init__(self, key, payload=None):
        self.id = key
        self._payload = payload

    @property
    def exists(self):
        return self._payload is not None

    def to_dict(self):
        return dict(self._payload or {})


class FakeDocument:
    def __init__(self, store, key):
        self.store = store
        self.key = key

    def get(self):
        return FakeSnapshot(self.key, self.store.get(self.key))

    def create(self, payload):
        if self.key in self.store:
            raise AlreadyExists("already exists")
        self.store[self.key] = dict(payload)

    def set(self, payload, merge=False):
        if merge and self.key in self.store:
            current = dict(self.store[self.key])
            current.update(payload)
            self.store[self.key] = current
        else:
            self.store[self.key] = dict(payload)


class FakeCollection:
    def __init__(self, store):
        self.store = store

    def document(self, key):
        return FakeDocument(self.store, key)


class FakeFirestore:
    def __init__(self, manual_initial=None):
        self.collections = {
            manual_store.MANUAL_COLLECTION: dict(manual_initial or {}),
            manual_store.SYSTEM_COLLECTION: {},
        }

    @property
    def store(self):
        return self.collections[manual_store.MANUAL_COLLECTION]

    def collection(self, name):
        return FakeCollection(self.collections.setdefault(name, {}))


class ManualStoreMigrationTests(unittest.TestCase):
    def setUp(self):
        with manual_store._migration_lock:
            manual_store._migration_status.update({
                "attempted": False,
                "source": "bundled_legacy_snapshot",
                "loaded_count": 0,
                "created_count": 0,
                "existing_count": 0,
                "invalid_count": 0,
                "error_count": 0,
                "completed": False,
                "error": "",
            })

    def test_migration_never_overwrites_existing_firestore_address(self):
        existing_biz = "3120813966"
        new_biz = "3120813705"
        client = FakeFirestore({
            existing_biz: {
                "biz_no": existing_biz,
                "address": "Firestore 기존주소",
                "company_name": "전진유리",
            }
        })
        legacy = {
            existing_biz: {
                "address": "GitHub 옛주소",
                "company_name": "전진유리",
                "updated_at": "2026-09-04T06:54:42+00:00",
            },
            new_biz: {
                "address": "충청남도 천안시 동남구 천안천공원길 1",
                "company_name": "구룡문구서점",
                "updated_at": "2026-09-04T06:50:18+00:00",
            },
        }

        with patch.object(manual_store, "_firestore_client", return_value=client), patch.object(
            manual_store, "_load_legacy_manual_addresses", return_value=legacy
        ):
            result = manual_store.migrate_legacy_manual_addresses()

        self.assertTrue(result["completed"])
        self.assertEqual(result["existing_count"], 1)
        self.assertEqual(result["created_count"], 1)
        self.assertEqual(client.store[existing_biz]["address"], "Firestore 기존주소")
        self.assertEqual(
            client.store[new_biz]["address"],
            "충청남도 천안시 동남구 천안천공원길 1",
        )
        self.assertEqual(client.store[new_biz]["migrated_from"], "github_legacy_snapshot")
        marker = client.collections[manual_store.SYSTEM_COLLECTION][manual_store.MIGRATION_DOC_ID]
        self.assertTrue(marker["completed"])


if __name__ == "__main__":
    unittest.main()
