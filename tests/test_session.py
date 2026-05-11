"""Tests for session management and OAuth authentication."""

import hmac
import json
import time
import unittest
from hashlib import sha256
from unittest.mock import patch, MagicMock
from urllib.parse import urlparse, parse_qs

from shopify_api import ShopSession, AuthenticationError, ResourceBase


class TestSessionSetup(unittest.TestCase):
    """Test global session configuration."""

    def setUp(self):
        ShopSession._api_key = None
        ShopSession._secret_key = None
        ShopSession._protocol = "https"
        ShopSession._domain_suffix = "myshopify.com"
        ShopSession._port = None

    def test_setup_stores_api_credentials(self):
        ShopSession.setup(api_key="test_key", secret="test_secret")
        self.assertEqual("test_key", ShopSession._api_key)
        self.assertEqual("test_secret", ShopSession._secret_key)

    def test_setup_allows_custom_protocol(self):
        ShopSession.setup(protocol="http")
        self.assertEqual("http", ShopSession._protocol)

    def test_setup_allows_custom_domain(self):
        ShopSession.setup(domain_suffix="shopify.local")
        self.assertEqual("shopify.local", ShopSession._domain_suffix)

    def test_setup_allows_custom_port(self):
        ShopSession.setup(port=3000)
        self.assertEqual(3000, ShopSession._port)


class TestSessionCreation(unittest.TestCase):
    """Test session initialization and URL normalization."""

    def setUp(self):
        ShopSession._api_key = "test_key"
        ShopSession._secret_key = "test_secret"
        ShopSession._protocol = "https"
        ShopSession._domain_suffix = "myshopify.com"
        ShopSession._port = None

    def test_create_session_with_full_url(self):
        session = ShopSession("https://testshop.myshopify.com", "2024-07", "token123")
        self.assertEqual("testshop.myshopify.com", session.shop_domain)

    def test_create_session_with_subdomain_only(self):
        session = ShopSession("testshop", "2024-07", "token123")
        self.assertEqual("testshop.myshopify.com", session.shop_domain)

    def test_create_session_with_http_url(self):
        session = ShopSession("http://testshop.different.com", "unstable", "token")
        self.assertEqual("testshop.myshopify.com", session.shop_domain)

    def test_create_session_with_path_in_url(self):
        session = ShopSession("https://user:pass@testshop.example.com/path", "2024-07", "token")
        self.assertEqual("testshop.myshopify.com", session.shop_domain)

    def test_empty_url_returns_none(self):
        session = ShopSession("", "2024-07", "token")
        self.assertIsNone(session.shop_domain)

    def test_whitespace_url_returns_none(self):
        session = ShopSession("   ", "2024-07", "token")
        self.assertIsNone(session.shop_domain)


class TestSessionValidation(unittest.TestCase):
    """Test session validity checks."""

    def setUp(self):
        ShopSession._domain_suffix = "myshopify.com"
        ShopSession._port = None

    def test_session_valid_with_url_and_token(self):
        session = ShopSession("testshop.myshopify.com", "2024-07", "token123")
        self.assertTrue(session.valid)

    def test_session_invalid_without_token(self):
        session = ShopSession("testshop.myshopify.com", "2024-07")
        self.assertFalse(session.valid)

    def test_session_invalid_without_url(self):
        session = ShopSession("", "2024-07", "token123")
        self.assertFalse(session.valid)


class TestSessionSite(unittest.TestCase):
    """Test site URL generation."""

    def setUp(self):
        ShopSession._protocol = "https"
        ShopSession._domain_suffix = "myshopify.com"
        ShopSession._port = None

    def test_site_url_with_version(self):
        session = ShopSession("testshop", "2024-07", "token")
        self.assertEqual("https://testshop.myshopify.com/admin/api/2024-07", session.site)

    def test_site_url_with_unstable_version(self):
        session = ShopSession("testshop", "unstable", "token")
        self.assertEqual("https://testshop.myshopify.com/admin/api/unstable", session.site)

    def test_site_url_with_custom_port(self):
        ShopSession._port = 3000
        session = ShopSession("testshop", "2024-07", "token")
        self.assertEqual("https://testshop.myshopify.com:3000/admin/api/2024-07", session.site)
        ShopSession._port = None


class TestPermissionUrl(unittest.TestCase):
    """Test OAuth permission URL generation."""

    def setUp(self):
        ShopSession.setup(api_key="test_api_key", secret="test_secret")
        ShopSession._domain_suffix = "myshopify.com"
        ShopSession._port = None

    def test_permission_url_with_redirect_only(self):
        session = ShopSession("testshop", "2024-07")
        url = session.create_permission_url("https://myapp.com/callback")

        parsed = urlparse(url)
        params = parse_qs(parsed.query)

        self.assertEqual("testshop.myshopify.com", parsed.netloc)
        self.assertEqual("/admin/oauth/authorize", parsed.path)
        self.assertEqual(["test_api_key"], params["client_id"])
        self.assertEqual(["https://myapp.com/callback"], params["redirect_uri"])

    def test_permission_url_with_single_scope(self):
        session = ShopSession("testshop", "2024-07")
        url = session.create_permission_url("https://myapp.com/callback", scope=["read_products"])

        params = parse_qs(urlparse(url).query)
        self.assertEqual(["read_products"], params["scope"])

    def test_permission_url_with_multiple_scopes(self):
        session = ShopSession("testshop", "2024-07")
        url = session.create_permission_url("https://myapp.com/callback", scope=["read_products", "write_orders"])

        params = parse_qs(urlparse(url).query)
        self.assertEqual(["read_products,write_orders"], params["scope"])

    def test_permission_url_with_empty_scope(self):
        session = ShopSession("testshop", "2024-07")
        url = session.create_permission_url("https://myapp.com/callback", scope=[])

        params = parse_qs(urlparse(url).query)
        self.assertNotIn("scope", params)

    def test_permission_url_with_state(self):
        session = ShopSession("testshop", "2024-07")
        url = session.create_permission_url("https://myapp.com/callback", state="csrf_token_123")

        params = parse_qs(urlparse(url).query)
        self.assertEqual(["csrf_token_123"], params["state"])

    def test_permission_url_with_scope_and_state(self):
        session = ShopSession("testshop", "2024-07")
        url = session.create_permission_url(
            "https://myapp.com/callback",
            scope=["read_products"],
            state="mystate"
        )

        params = parse_qs(urlparse(url).query)
        self.assertEqual(["read_products"], params["scope"])
        self.assertEqual(["mystate"], params["state"])


class TestHmacValidation(unittest.TestCase):
    """Test HMAC calculation and validation."""

    def setUp(self):
        ShopSession.setup(api_key="test_key", secret="hush")

    def test_calculate_hmac_matches_shopify_example(self):
        params = {
            "shop": "some-shop.myshopify.com",
            "code": "a94a110d86d2452eb3e2af4cfb8a3828",
            "timestamp": "1337178173",
        }
        expected_hmac = "2cb1a277650a659f1b11e92a4a64275b128e037f2c3390e3c8fd2d8721dac9e2"
        self.assertEqual(expected_hmac, ShopSession.calculate_hmac(params))

    def test_validate_hmac_with_correct_signature(self):
        params = {
            "shop": "some-shop.myshopify.com",
            "code": "a94a110d86d2452eb3e2af4cfb8a3828",
            "timestamp": "1337178173",
            "hmac": "2cb1a277650a659f1b11e92a4a64275b128e037f2c3390e3c8fd2d8721dac9e2",
        }
        self.assertTrue(ShopSession.validate_hmac(params))

    def test_validate_hmac_with_wrong_signature(self):
        params = {
            "shop": "some-shop.myshopify.com",
            "code": "a94a110d86d2452eb3e2af4cfb8a3828",
            "timestamp": "1337178173",
            "hmac": "wrong_hmac_signature",
        }
        self.assertFalse(ShopSession.validate_hmac(params))

    def test_validate_hmac_without_hmac_param(self):
        params = {
            "shop": "some-shop.myshopify.com",
            "code": "a94a110d86d2452eb3e2af4cfb8a3828",
        }
        self.assertFalse(ShopSession.validate_hmac(params))

    def test_hmac_with_special_characters(self):
        ShopSession.setup(secret="secret")
        params = {"a": "1&b=2", "c=3&d": "4"}
        to_sign = "a=1%26b=2&c%3D3%26d=4"
        expected_hmac = hmac.new("secret".encode(), to_sign.encode(), sha256).hexdigest()
        self.assertEqual(expected_hmac, ShopSession.calculate_hmac(params))

    def test_hmac_with_array_parameters(self):
        ShopSession.setup(secret="hush")
        params = {
            "shop": "some-shop.myshopify.com",
            "ids[]": [2, 1],
            "hmac": "b93b9f82996f6f8bf9f1b7bbddec284c8fabacdc4e12dc80550b4705f3003b1e",
        }
        self.assertTrue(ShopSession.validate_hmac(params))


class TestParamsValidation(unittest.TestCase):
    """Test OAuth callback parameter validation."""

    def setUp(self):
        ShopSession.setup(api_key="test_key", secret="secret")

    def test_validate_params_with_valid_params(self):
        params = {"code": "any-code", "timestamp": str(int(time.time()))}
        params["hmac"] = ShopSession.calculate_hmac(params)
        self.assertTrue(ShopSession.validate_params(params))

    def test_validate_params_rejects_old_timestamp(self):
        one_day_seconds = 24 * 60 * 60
        old_time = int(time.time()) - (2 * one_day_seconds)
        params = {"code": "any-code", "timestamp": str(old_time)}
        params["hmac"] = ShopSession.calculate_hmac(params)
        self.assertFalse(ShopSession.validate_params(params))

    def test_validate_params_without_timestamp(self):
        params = {"code": "any-code"}
        params["hmac"] = ShopSession.calculate_hmac(params)
        self.assertFalse(ShopSession.validate_params(params))


class TestRequestToken(unittest.TestCase):
    """Test OAuth token exchange."""

    def setUp(self):
        ShopSession.setup(api_key="test_key", secret="secret")
        ShopSession._domain_suffix = "myshopify.com"

    def test_request_token_returns_existing_token(self):
        session = ShopSession("testshop", "2024-07", "existing_token")
        token = session.request_token({})
        self.assertEqual("existing_token", token)

    def test_request_token_raises_on_invalid_hmac(self):
        session = ShopSession("testshop", "2024-07")
        params = {"code": "some_code", "timestamp": str(int(time.time())), "hmac": "invalid"}

        with self.assertRaises(AuthenticationError) as context:
            session.request_token(params)

        self.assertIn("Invalid HMAC", str(context.exception))

    @patch("shopify_api.session.urlopen")
    def test_request_token_exchanges_code_for_token(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "access_token": "new_token",
            "scope": "read_products,write_orders"
        }).encode("utf-8")
        mock_urlopen.return_value = mock_response

        session = ShopSession("testshop", "2024-07")
        params = {"code": "auth_code", "timestamp": str(int(time.time()))}
        params["hmac"] = ShopSession.calculate_hmac(params)

        token = session.request_token(params)

        self.assertEqual("new_token", token)
        self.assertEqual("new_token", session.token)
        self.assertEqual("read_products,write_orders", session.scopes)


class TestTempSession(unittest.TestCase):
    """Test temporary session context manager."""

    def setUp(self):
        ShopSession.setup(api_key="test_key", secret="secret")
        ShopSession._domain_suffix = "myshopify.com"
        ShopSession._port = None
        ResourceBase.clear_session()

    def test_temp_session_activates_session(self):
        original_site = ResourceBase.get_site()

        with ShopSession.temp("testshop", "2024-07", "temp_token"):
            active_site = ResourceBase.get_site()
            self.assertEqual("https://testshop.myshopify.com/admin/api/2024-07", active_site)

        self.assertEqual(original_site, ResourceBase.get_site())

    def test_temp_session_sets_headers(self):
        with ShopSession.temp("testshop", "2024-07", "temp_token"):
            headers = ResourceBase.get_headers()
            self.assertEqual("temp_token", headers.get("X-Shopify-Access-Token"))

    def test_temp_session_restores_previous_session(self):
        first_session = ShopSession("shop1", "2024-07", "token1")
        ResourceBase.set_active_session(first_session)

        with ShopSession.temp("shop2", "unstable", "token2"):
            self.assertEqual("https://shop2.myshopify.com/admin/api/unstable", ResourceBase.get_site())

        self.assertEqual("https://shop1.myshopify.com/admin/api/2024-07", ResourceBase.get_site())


if __name__ == "__main__":
    unittest.main()
