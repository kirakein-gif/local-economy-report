import unittest
from unittest.mock import patch

from google.api_core.exceptions import AlreadyExists

from app import manual_store


class FakeDocument:
    def __init__(self, store, key):
        self.store = store
        self.key = key

    def create(self, payload):
        if self.key in self.store:
            raise AlreadyExists("already exists")
        self.store[self.key] = dict(payload)


class FakeCollection:
    def __init__(self, store):
        self.store = store

    def document(self, key):
        return FakeDocument(self.store, key)


class FakeFirestore:
    def __init__(self, initial=None):
        self.store = dict(initial or {})

    def collection(self, name):
        return FakeCollection(self.store)


class ManualStoreMigrationTests(unittest.TestCase):
    def setUp(self):
        with manual_store._migration_lock:
            manual_store._migration_status.update({
                "attempted": False,
                "source": "github_legacy",
                "loaded_count": 0,
                "created_count": 0,
                "existing_count": 0,
                "invalid_count": 0,
                "error_count": 0,
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

        self.assertEqual(result["existing_count"], 1)
        self.assertEqual(result["created_count"], 1)
        self.assertEqual(client.store[existing_biz]["address"], "Firestore 기존주소")
        self.assertEqual(
            client.store[new_biz]["address"],
            "충청남도 천안시 동남구 천안천공원길 1",
        )
        self.assertEqual(client.store[new_biz]["migrated_from"], "github_legacy")


if __name__ == "__main__":
    unittest.main()
