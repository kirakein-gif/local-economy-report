import unittest
from unittest.mock import patch

from app import address_service, manual_store
from app.cache import address_cache


class AddressServiceTests(unittest.TestCase):
    def setUp(self):
        with address_cache._lock:
            address_cache._local.clear()
        with manual_store._local_lock:
            manual_store._local_manual.clear()

    def test_invalid_business_number(self):
        result = address_service.lookup_address("123")
        self.assertFalse(result["found"])
        self.assertTrue(result["invalid"])

    @patch.object(address_service, "get_local_franchise_address", return_value=None)
    @patch.object(address_service, "get_ftc_mail_order_address", return_value=None)
    @patch.object(address_service, "get_s2b_address", return_value=None)
    @patch.object(address_service, "get_procurement_address", return_value=None)
    def test_saved_manual_address_is_only_suggestion_after_public_sources_fail(self, *_):
        manual_store.save_manual_address(
            "123-45-67890",
            "충청남도 천안시 저장주소 10",
            "테스트업체",
        )

        result = address_service.lookup_address("1234567890", force_refresh=True)

        self.assertFalse(result["found"])
        self.assertFalse(result["manual_hit"])
        self.assertTrue(result["manual_suggestion"])
        self.assertEqual(result["saved_address"], "충청남도 천안시 저장주소 10")
        self.assertEqual(result["saved_company_name"], "테스트업체")
        self.assertEqual(result["address"], "")

    @patch.object(address_service, "get_local_franchise_address", return_value=None)
    @patch.object(address_service, "get_ftc_mail_order_address", return_value=None)
    @patch.object(address_service, "get_s2b_address", return_value=None)
    @patch.object(address_service, "get_procurement_address", return_value="충청남도 천안시 API주소 1")
    def test_public_api_wins_over_saved_manual_address(self, procurement, *_):
        manual_store.save_manual_address(
            "123-45-67890",
            "충청남도 천안시 사용자입력 99",
            "테스트업체",
        )

        result = address_service.lookup_address("1234567890", force_refresh=True)

        self.assertTrue(result["found"])
        self.assertEqual(result["source"], "나라장터")
        self.assertEqual(result["address"], "충청남도 천안시 API주소 1")
        self.assertFalse(result["manual_suggestion"])
        procurement.assert_called_once()

    @patch.object(address_service, "get_local_franchise_address", return_value=None)
    @patch.object(address_service, "get_ftc_mail_order_address", return_value=None)
    @patch.object(address_service, "get_s2b_address", return_value=None)
    @patch.object(address_service, "get_procurement_address", return_value="충청남도 천안시 테스트로 1")
    def test_positive_public_result_is_cached_and_reused(self, procurement, *_):
        first = address_service.lookup_address("123-45-67890")
        manual_store.save_manual_address(
            "1234567890",
            "충청남도 천안시 사용자입력 99",
            "테스트업체",
        )
        second = address_service.lookup_address("1234567890")

        self.assertTrue(first["found"])
        self.assertEqual(first["source"], "나라장터")
        self.assertFalse(first["cache_hit"])

        self.assertTrue(second["found"])
        self.assertTrue(second["cache_hit"])
        self.assertEqual(second["source"], "나라장터")
        self.assertEqual(second["address"], "충청남도 천안시 테스트로 1")
        self.assertFalse(second["manual_suggestion"])
        self.assertEqual(procurement.call_count, 1)

    @patch.object(address_service, "get_local_franchise_address", return_value=None)
    @patch.object(address_service, "get_ftc_mail_order_address", return_value=None)
    @patch.object(address_service, "get_s2b_address", return_value="충청남도 아산시 테스트길 2")
    @patch.object(address_service, "get_procurement_address", return_value=None)
    def test_source_order_falls_back_to_s2b(self, *_):
        result = address_service.lookup_address("1112233333", force_refresh=True)

        self.assertTrue(result["found"])
        self.assertEqual(result["source"], "학교장터(S2B)")

    @patch.object(address_service, "_lookup_public_sources")
    def test_bulk_deduplicates_business_numbers(self, lookup):
        lookup.side_effect = lambda biz, manual=None, progress_callback=None, *args, **kwargs: {
            "biz_no": biz,
            "address": "충남",
            "source": "나라장터",
            "found": True,
            "cache_hit": False,
            "cache_layer": "",
            "cache_backend": "memory",
            "manual_hit": False,
            "manual_suggestion": False,
            "saved_address": "",
            "saved_company_name": "",
            "invalid": False,
        }

        result = address_service.bulk_lookup_addresses(
            ["123-45-67890", "1234567890", "111-22-33333"]
        )

        self.assertEqual(result["requested_count"], 3)
        self.assertEqual(result["unique_valid_count"], 2)
        self.assertEqual(result["found_count"], 2)
        self.assertEqual(result["manual_suggestion_count"], 0)
        self.assertEqual(lookup.call_count, 2)

    @patch.object(address_service, "_lookup_public_sources")
    def test_bulk_reports_truthful_completion_progress(self, lookup):
        lookup.side_effect = lambda biz, manual=None, progress_callback=None, *args, **kwargs: {
            "biz_no": biz,
            "address": "충남",
            "source": "나라장터",
            "found": True,
            "cache_hit": False,
            "cache_layer": "",
            "cache_backend": "memory",
            "manual_hit": False,
            "manual_suggestion": False,
            "saved_address": "",
            "saved_company_name": "",
            "invalid": False,
        }
        events = []

        result = address_service.bulk_lookup_addresses(
            ["1234567890", "1112233333"],
            progress_callback=events.append,
        )

        self.assertEqual(result["found_count"], 2)
        self.assertEqual(events[0]["type"], "start")
        completes = [event for event in events if event.get("type") == "complete"]
        self.assertEqual(len(completes), 2)
        self.assertEqual(completes[-1]["completed"], 2)
        self.assertEqual(completes[-1]["total"], 2)


    def test_positive_cache_uses_thirty_day_ttl(self):
        from app.cache import DEFAULT_POSITIVE_TTL, DEFAULT_POSITIVE_TTL_DAYS

        self.assertEqual(DEFAULT_POSITIVE_TTL_DAYS, 30)
        self.assertEqual(DEFAULT_POSITIVE_TTL, 30 * 86400)

    @patch.object(address_service, "get_local_franchise_address", return_value=None)
    @patch.object(address_service, "get_ftc_mail_order_address", return_value=None)
    @patch.object(address_service, "get_s2b_address", return_value="충청남도 아산시 재확인주소")
    @patch.object(address_service, "get_procurement_address", return_value=None)
    def test_stale_cache_rechecks_original_source_first(
        self,
        procurement,
        s2b,
        ftc,
        franchise,
    ):
        stale = {
            "address": "충청남도 아산시 기존주소",
            "source": "학교장터(S2B)",
            "found": True,
            "updated_at": 1,
            "verified_at": 1,
            "expires_at": 1,
        }
        with address_cache._lock:
            address_cache._local["1234567890"] = dict(stale)

        result = address_service.lookup_address("1234567890")

        self.assertTrue(result["found"])
        self.assertEqual(result["source"], "학교장터(S2B)")
        self.assertEqual(result["address"], "충청남도 아산시 재확인주소")
        s2b.assert_called_once()
        procurement.assert_not_called()
        ftc.assert_not_called()
        franchise.assert_not_called()

    def test_cache_preserves_previous_address_when_verified_address_changes(self):
        previous = {
            "address": "충청남도 천안시 이전주소 1",
            "source": "나라장터",
            "found": True,
            "verified_at": 100,
            "updated_at": 100,
            "expires_at": 101,
        }

        payload = address_cache.set(
            "1234567890",
            address="충청남도 천안시 새주소 2",
            source="나라장터",
            found=True,
            ttl_seconds=30 * 86400,
            previous_item=previous,
        )

        self.assertEqual(payload["previous_address"], "충청남도 천안시 이전주소 1")
        self.assertEqual(payload["previous_source"], "나라장터")
        self.assertIn("changed_at", payload)
        self.assertIn("verified_at", payload)


    @patch.object(address_service, "get_local_franchise_address", return_value=None)
    @patch.object(address_service, "get_ftc_mail_order_address", return_value=None)
    @patch.object(address_service, "get_s2b_address", return_value=None)
    @patch.object(address_service, "get_procurement_address", return_value=None)
    def test_failed_revalidation_keeps_last_verified_address_for_retry(self, *_):
        stale = {
            "address": "충청남도 천안시 마지막확인주소",
            "source": "나라장터",
            "found": True,
            "updated_at": 100,
            "verified_at": 100,
            "expires_at": 1,
        }
        with address_cache._lock:
            address_cache._local["1234567890"] = dict(stale)

        result = address_service.lookup_address("1234567890")

        self.assertTrue(result["found"])
        self.assertTrue(result["stale"])
        self.assertTrue(result["revalidation_failed"])
        self.assertEqual(result["address"], "충청남도 천안시 마지막확인주소")
        cached = address_cache.get("1234567890")
        self.assertIsNotNone(cached)
        self.assertEqual(cached["verified_at"], 100)
        self.assertIn("revalidation_failed_at", cached)


if __name__ == "__main__":
    unittest.main()
