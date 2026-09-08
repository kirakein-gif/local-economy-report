import unittest
from unittest.mock import patch

from app import address_service
from app.cache import address_cache


class AddressServiceTests(unittest.TestCase):
    def setUp(self):
        with address_cache._lock:
            address_cache._local.clear()

    def test_invalid_business_number(self):
        result = address_service.lookup_address("123")
        self.assertFalse(result["found"])
        self.assertTrue(result["invalid"])

    @patch.object(address_service, "get_local_franchise_address", return_value=None)
    @patch.object(address_service, "get_ftc_mail_order_address", return_value=None)
    @patch.object(address_service, "get_s2b_address", return_value=None)
    @patch.object(address_service, "get_procurement_address", return_value="충청남도 천안시 테스트로 1")
    def test_positive_result_is_cached(self, procurement, *_):
        first = address_service.lookup_address("123-45-67890")
        second = address_service.lookup_address("1234567890")

        self.assertTrue(first["found"])
        self.assertEqual(first["source"], "나라장터")
        self.assertFalse(first["cache_hit"])

        self.assertTrue(second["found"])
        self.assertTrue(second["cache_hit"])
        self.assertEqual(second["address"], "충청남도 천안시 테스트로 1")
        self.assertEqual(procurement.call_count, 1)

    @patch.object(address_service, "get_local_franchise_address", return_value=None)
    @patch.object(address_service, "get_ftc_mail_order_address", return_value=None)
    @patch.object(address_service, "get_s2b_address", return_value="충청남도 아산시 테스트길 2")
    @patch.object(address_service, "get_procurement_address", return_value=None)
    def test_source_order_falls_back_to_s2b(self, *_):
        result = address_service.lookup_address("1112233333", force_refresh=True)

        self.assertTrue(result["found"])
        self.assertEqual(result["source"], "학교장터(S2B)")

    @patch.object(address_service, "lookup_address")
    def test_bulk_deduplicates_business_numbers(self, lookup):
        lookup.side_effect = lambda biz, force_refresh=False: {
            "biz_no": biz,
            "address": "충남",
            "source": "나라장터",
            "found": True,
            "cache_hit": False,
            "cache_layer": "",
            "cache_backend": "memory",
            "invalid": False,
        }

        result = address_service.bulk_lookup_addresses(
            ["123-45-67890", "1234567890", "111-22-33333"]
        )

        self.assertEqual(result["requested_count"], 3)
        self.assertEqual(result["unique_valid_count"], 2)
        self.assertEqual(result["found_count"], 2)


if __name__ == "__main__":
    unittest.main()
