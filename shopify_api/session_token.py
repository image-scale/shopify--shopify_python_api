"""Session token validation for Shopify embedded apps.

Shopify embedded apps use JWT-based session tokens for authentication.
This module provides functions to decode and validate these tokens.
"""

import re
from urllib.parse import urljoin, urlparse

import jwt


ALGORITHM = "HS256"
BEARER_PREFIX = "Bearer "
REQUIRED_FIELDS = ["iss", "dest", "sub", "jti", "sid"]
LEEWAY_SECONDS = 10
HOSTNAME_PATTERN = r"[a-z0-9][a-z0-9-]*[a-z0-9]"


class SessionTokenError(Exception):
    """Base exception for session token errors."""
    pass


class TokenAuthenticationError(SessionTokenError):
    """Raised when the authorization header format is invalid."""
    pass


class InvalidIssuerError(SessionTokenError):
    """Raised when the token issuer is not a valid Shopify domain."""
    pass


class MismatchedHostsError(SessionTokenError):
    """Raised when the issuer and destination hosts don't match."""
    pass


def decode_from_header(authorization_header, api_key, secret):
    """Decode and validate a session token from an Authorization header.

    Args:
        authorization_header: The HTTP Authorization header value (Bearer token)
        api_key: The Shopify app API key (used as audience)
        secret: The Shopify app API secret (used to verify signature)

    Returns:
        Dict containing the decoded JWT payload

    Raises:
        TokenAuthenticationError: If the header doesn't contain a Bearer token
        SessionTokenError: If the token is invalid, expired, or has wrong audience
        InvalidIssuerError: If the issuer is not a valid Shopify domain
        MismatchedHostsError: If the issuer and destination don't match
    """
    session_token = _extract_session_token(authorization_header)
    decoded_payload = _decode_session_token(session_token, api_key, secret)
    _validate_issuer(decoded_payload)

    return decoded_payload


def _extract_session_token(authorization_header):
    """Extract the JWT from a Bearer token header."""
    if not authorization_header.startswith(BEARER_PREFIX):
        raise TokenAuthenticationError(
            "The Authorization header does not contain a Bearer token"
        )

    return authorization_header[len(BEARER_PREFIX):]


def _decode_session_token(session_token, api_key, secret):
    """Decode and validate a JWT session token."""
    try:
        return jwt.decode(
            session_token,
            secret,
            audience=api_key,
            algorithms=[ALGORITHM],
            leeway=LEEWAY_SECONDS,
            options={"require": REQUIRED_FIELDS},
        )
    except jwt.exceptions.PyJWTError as e:
        raise SessionTokenError(str(e)) from e


def _validate_issuer(decoded_payload):
    """Validate the issuer claims in the token."""
    _validate_issuer_hostname(decoded_payload)
    _validate_issuer_dest_match(decoded_payload)


def _validate_issuer_hostname(decoded_payload):
    """Validate that the issuer is a valid Shopify shop domain."""
    issuer = decoded_payload["iss"]
    issuer_root = urljoin(issuer, "/")

    if not _is_valid_shop_domain(issuer_root):
        raise InvalidIssuerError("Invalid issuer")


def _validate_issuer_dest_match(decoded_payload):
    """Validate that the issuer and destination hosts match."""
    issuer_root = urljoin(decoded_payload["iss"], "/")
    dest_root = urljoin(decoded_payload["dest"], "/")

    if issuer_root != dest_root:
        raise MismatchedHostsError("The issuer and destination do not match")


def _is_valid_shop_domain(url, myshopify_domain="myshopify.com"):
    """Check if a URL is a valid Shopify shop domain.

    Args:
        url: The URL to validate
        myshopify_domain: The expected domain suffix

    Returns:
        True if the URL is a valid shop domain
    """
    parsed = urlparse(url)
    hostname = parsed.netloc.lower()

    pattern = r"^{h}\.{d}$".format(
        h=HOSTNAME_PATTERN,
        d=re.escape(myshopify_domain)
    )

    return bool(re.match(pattern, hostname))
