"""Tests for API call limit tracking."""

import unittest
from unittest.mock import MagicMock, patch

from shopify_api import ShopSession, ResourceBase, Limits, LimitsError


class TestLimits(unittest.TestCase):
    """Test API call limit tracking."""

    def setUp(self):
        ResourceBase.clear_session()
        session = ShopSession("testshop", "2024-07", "token123")
        ResourceBase.activate_session(session)

    def tearDown(self):
        ResourceBase.clear_session()

    def test_raises_error_when_no_response(self):
        ResourceBase._response = None

        with self.assertRaises(LimitsError) as context:
            Limits.credit_left()

        self.assertIn("No response", str(context.exception))

    def test_raises_error_when_no_headers(self):
        mock_response = MagicMock()
        mock_response.headers = {}
        ResourceBase._response = mock_response

        with self.assertRaises(LimitsError) as context:
            Limits.credit_left()

        self.assertIn("No API call limit header", str(context.exception))

    def test_credit_limit_returns_total(self):
        mock_response = MagicMock()
        mock_response.headers = {"X-Shopify-Shop-Api-Call-Limit": "40/40"}
        ResourceBase._response = mock_response

        self.assertEqual(40, Limits.credit_limit())

    def test_credit_limit_with_larger_bucket(self):
        mock_response = MagicMock()
        mock_response.headers = {"X-Shopify-Shop-Api-Call-Limit": "100/300"}
        ResourceBase._response = mock_response

        self.assertEqual(300, Limits.credit_limit())

    def test_credit_used_returns_used_calls(self):
        mock_response = MagicMock()
        mock_response.headers = {"X-Shopify-Shop-Api-Call-Limit": "1/40"}
        ResourceBase._response = mock_response

        self.assertEqual(1, Limits.credit_used())

    def test_credit_used_with_many_calls(self):
        mock_response = MagicMock()
        mock_response.headers = {"X-Shopify-Shop-Api-Call-Limit": "292/300"}
        ResourceBase._response = mock_response

        self.assertEqual(292, Limits.credit_used())

    def test_credit_left_calculates_remaining(self):
        mock_response = MagicMock()
        mock_response.headers = {"X-Shopify-Shop-Api-Call-Limit": "292/300"}
        ResourceBase._response = mock_response

        self.assertEqual(8, Limits.credit_left())

    def test_credit_left_when_fresh(self):
        mock_response = MagicMock()
        mock_response.headers = {"X-Shopify-Shop-Api-Call-Limit": "1/40"}
        ResourceBase._response = mock_response

        self.assertEqual(39, Limits.credit_left())

    def test_credit_maxed_returns_false_when_available(self):
        mock_response = MagicMock()
        mock_response.headers = {"X-Shopify-Shop-Api-Call-Limit": "125/300"}
        ResourceBase._response = mock_response

        self.assertFalse(Limits.credit_maxed())

    def test_credit_maxed_returns_true_when_at_limit(self):
        mock_response = MagicMock()
        mock_response.headers = {"X-Shopify-Shop-Api-Call-Limit": "40/40"}
        ResourceBase._response = mock_response

        self.assertTrue(Limits.credit_maxed())

    def test_credit_maxed_returns_true_when_over_limit(self):
        mock_response = MagicMock()
        mock_response.headers = {"X-Shopify-Shop-Api-Call-Limit": "41/40"}
        ResourceBase._response = mock_response

        self.assertTrue(Limits.credit_maxed())

    def test_retry_after_returns_none_when_not_present(self):
        mock_response = MagicMock()
        mock_response.headers = {"X-Shopify-Shop-Api-Call-Limit": "40/40"}
        ResourceBase._response = mock_response

        self.assertIsNone(Limits.retry_after())

    def test_retry_after_returns_value_when_present(self):
        mock_response = MagicMock()
        mock_response.headers = {
            "X-Shopify-Shop-Api-Call-Limit": "40/40",
            "Retry-After": "2.5"
        }
        ResourceBase._response = mock_response

        self.assertEqual(2.5, Limits.retry_after())


class TestLimitsHeaderVariations(unittest.TestCase):
    """Test various header formats."""

    def setUp(self):
        ResourceBase.clear_session()
        session = ShopSession("testshop", "2024-07", "token123")
        ResourceBase.activate_session(session)

    def tearDown(self):
        ResourceBase.clear_session()

    def test_lowercase_header_name(self):
        mock_response = MagicMock()
        mock_response.headers = {"x-shopify-shop-api-call-limit": "10/40"}
        ResourceBase._response = mock_response

        self.assertEqual(10, Limits.credit_used())
        self.assertEqual(40, Limits.credit_limit())

    def test_mixed_case_header_name(self):
        mock_response = MagicMock()
        mock_response.headers = {"x-Shopify-Shop-Api-Call-Limit": "15/40"}
        ResourceBase._response = mock_response

        self.assertEqual(15, Limits.credit_used())


if __name__ == "__main__":
    unittest.main()
