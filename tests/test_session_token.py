"""Tests for session token validation."""

import unittest
from datetime import datetime, timedelta

import jwt

from shopify_api.session_token import (
    decode_from_header,
    SessionTokenError,
    TokenAuthenticationError,
    InvalidIssuerError,
    MismatchedHostsError,
)


def timestamp(date):
    return date.timestamp()


class TestSessionTokenDecode(unittest.TestCase):
    """Test session token decoding and validation."""

    def setUp(self):
        self.secret = "api_secret"
        self.api_key = "api_key"
        current_time = datetime.now()
        self.payload = {
            "iss": "https://test-shop.myshopify.com/admin",
            "dest": "https://test-shop.myshopify.com",
            "aud": self.api_key,
            "sub": "1",
            "exp": timestamp(current_time + timedelta(seconds=60)),
            "nbf": timestamp(current_time),
            "iat": timestamp(current_time),
            "jti": "4321",
            "sid": "abc123",
        }

    def build_auth_header(self):
        token = jwt.encode(self.payload, self.secret, algorithm="HS256")
        return f"Bearer {token}"

    def test_returns_decoded_payload(self):
        result = decode_from_header(
            self.build_auth_header(),
            api_key=self.api_key,
            secret=self.secret
        )

        self.assertEqual(self.payload["iss"], result["iss"])
        self.assertEqual(self.payload["dest"], result["dest"])
        self.assertEqual(self.payload["sub"], result["sub"])
        self.assertEqual(self.payload["sid"], result["sid"])

    def test_raises_if_not_bearer_token(self):
        with self.assertRaises(TokenAuthenticationError) as context:
            decode_from_header("Basic abc123", self.api_key, self.secret)

        self.assertIn("Bearer", str(context.exception))

    def test_raises_if_token_expired(self):
        self.payload["exp"] = timestamp(datetime.now() - timedelta(seconds=60))

        with self.assertRaises(SessionTokenError) as context:
            decode_from_header(
                self.build_auth_header(),
                self.api_key,
                self.secret
            )

        self.assertIn("expired", str(context.exception).lower())

    def test_raises_if_invalid_signature(self):
        bad_token = jwt.encode(self.payload, "wrong_secret", algorithm="HS256")
        header = f"Bearer {bad_token}"

        with self.assertRaises(SessionTokenError) as context:
            decode_from_header(header, self.api_key, self.secret)

        self.assertIn("Signature", str(context.exception))

    def test_raises_if_audience_mismatch(self):
        self.payload["aud"] = "wrong_api_key"

        with self.assertRaises(SessionTokenError) as context:
            decode_from_header(
                self.build_auth_header(),
                self.api_key,
                self.secret
            )

        self.assertIn("Audience", str(context.exception))

    def test_raises_if_invalid_issuer_hostname(self):
        self.payload["iss"] = "https://invalid_hostname"

        with self.assertRaises(InvalidIssuerError) as context:
            decode_from_header(
                self.build_auth_header(),
                self.api_key,
                self.secret
            )

        self.assertIn("Invalid issuer", str(context.exception))

    def test_raises_if_issuer_and_dest_mismatch(self):
        self.payload["dest"] = "https://other-shop.myshopify.com"

        with self.assertRaises(MismatchedHostsError) as context:
            decode_from_header(
                self.build_auth_header(),
                self.api_key,
                self.secret
            )

        self.assertIn("do not match", str(context.exception))

    def test_allows_10_seconds_clock_skew(self):
        self.payload["nbf"] = timestamp(datetime.now() + timedelta(seconds=10))

        result = decode_from_header(
            self.build_auth_header(),
            self.api_key,
            self.secret
        )

        self.assertIsNotNone(result)

    def test_raises_if_invalid_algorithm(self):
        bad_token = jwt.encode(self.payload, None, algorithm="none")
        header = f"Bearer {bad_token}"

        with self.assertRaises(SessionTokenError):
            decode_from_header(header, self.api_key, self.secret)


class TestShopDomainValidation(unittest.TestCase):
    """Test shop domain validation."""

    def setUp(self):
        self.secret = "api_secret"
        self.api_key = "api_key"
        current_time = datetime.now()
        self.payload = {
            "iss": "https://my-shop.myshopify.com/admin",
            "dest": "https://my-shop.myshopify.com",
            "aud": self.api_key,
            "sub": "1",
            "exp": timestamp(current_time + timedelta(seconds=60)),
            "nbf": timestamp(current_time),
            "iat": timestamp(current_time),
            "jti": "1234",
            "sid": "session123",
        }

    def build_auth_header(self):
        token = jwt.encode(self.payload, self.secret, algorithm="HS256")
        return f"Bearer {token}"

    def test_accepts_valid_myshopify_domain(self):
        result = decode_from_header(
            self.build_auth_header(),
            self.api_key,
            self.secret
        )

        self.assertIsNotNone(result)

    def test_accepts_shop_with_numbers(self):
        self.payload["iss"] = "https://shop123.myshopify.com/admin"
        self.payload["dest"] = "https://shop123.myshopify.com"

        result = decode_from_header(
            self.build_auth_header(),
            self.api_key,
            self.secret
        )

        self.assertIsNotNone(result)

    def test_accepts_shop_with_dashes(self):
        self.payload["iss"] = "https://my-test-shop.myshopify.com/admin"
        self.payload["dest"] = "https://my-test-shop.myshopify.com"

        result = decode_from_header(
            self.build_auth_header(),
            self.api_key,
            self.secret
        )

        self.assertIsNotNone(result)

    def test_rejects_non_myshopify_domain(self):
        self.payload["iss"] = "https://example.com/admin"
        self.payload["dest"] = "https://example.com"

        with self.assertRaises(InvalidIssuerError):
            decode_from_header(
                self.build_auth_header(),
                self.api_key,
                self.secret
            )


if __name__ == "__main__":
    unittest.main()
