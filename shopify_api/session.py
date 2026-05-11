"""Shopify API session management with OAuth authentication."""

import hmac
import json
import re
import time
from contextlib import contextmanager
from hashlib import sha256
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError


class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass


class ShopSession:
    """Manages authentication and connection to a Shopify store.

    Handles OAuth flow, HMAC validation, and session lifecycle.
    """

    _api_key = None
    _secret_key = None
    _protocol = "https"
    _domain_suffix = "myshopify.com"
    _port = None

    @classmethod
    def setup(cls, api_key=None, secret=None, protocol=None, domain_suffix=None, port=None):
        """Configure global API credentials for all sessions.

        Args:
            api_key: The Shopify API key
            secret: The Shopify API secret key
            protocol: HTTP protocol to use (default: https)
            domain_suffix: Domain suffix (default: myshopify.com)
            port: Optional port number
        """
        if api_key is not None:
            cls._api_key = api_key
        if secret is not None:
            cls._secret_key = secret
        if protocol is not None:
            cls._protocol = protocol
        if domain_suffix is not None:
            cls._domain_suffix = domain_suffix
        if port is not None:
            cls._port = port

    @classmethod
    @contextmanager
    def temp(cls, shop_url, api_version, access_token):
        """Create a temporary session context.

        The session is automatically cleared when the context exits.

        Args:
            shop_url: The shop's URL or subdomain
            api_version: API version string (e.g., "2024-07")
            access_token: The access token for authentication

        Yields:
            The temporary ShopSession instance
        """
        from . import resource

        previous_state = resource.ResourceBase.get_session_state()

        session = cls(shop_url, api_version, access_token)
        resource.ResourceBase.set_active_session(session)

        try:
            yield session
        finally:
            resource.ResourceBase.restore_session_state(previous_state)

    def __init__(self, shop_url, api_version=None, access_token=None, scopes=None):
        """Initialize a session for a Shopify store.

        Args:
            shop_url: The shop's URL (can be full URL, domain, or just subdomain)
            api_version: API version string (e.g., "2024-07" or "unstable")
            access_token: OAuth access token for API requests
            scopes: OAuth scopes granted to this session
        """
        self._shop_domain = self._normalize_shop_url(shop_url)
        self._api_version = api_version
        self._access_token = access_token
        self._scopes = scopes

    @property
    def shop_domain(self):
        """The normalized shop domain."""
        return self._shop_domain

    @property
    def url(self):
        """Alias for shop_domain for compatibility."""
        return self._shop_domain

    @property
    def token(self):
        """The access token for this session."""
        return self._access_token

    @property
    def api_version(self):
        """The API version for this session."""
        return self._api_version

    @property
    def scopes(self):
        """The OAuth scopes for this session."""
        return self._scopes

    @scopes.setter
    def scopes(self, value):
        """Set the OAuth scopes."""
        self._scopes = value

    @property
    def valid(self):
        """Check if the session has required authentication data."""
        return self._shop_domain is not None and self._access_token is not None

    @property
    def site(self):
        """The full admin API URL for this session."""
        if self._shop_domain is None:
            return None
        base = f"{self._protocol}://{self._shop_domain}"
        return f"{base}/admin/api/{self._api_version}"

    def create_permission_url(self, redirect_uri, scope=None, state=None):
        """Generate the OAuth authorization URL.

        Args:
            redirect_uri: URL to redirect to after authorization
            scope: List of permission scopes to request
            state: Optional state parameter for CSRF protection

        Returns:
            The authorization URL to redirect the user to
        """
        params = {
            "client_id": self._api_key,
            "redirect_uri": redirect_uri,
        }

        if scope:
            params["scope"] = ",".join(scope)

        if state:
            params["state"] = state

        query = urlencode(params)
        return f"https://{self._shop_domain}/admin/oauth/authorize?{query}"

    def request_token(self, callback_params):
        """Exchange authorization code for access token.

        Args:
            callback_params: Dictionary of parameters from the OAuth callback

        Returns:
            The access token string

        Raises:
            AuthenticationError: If HMAC validation fails or token exchange fails
        """
        if self._access_token:
            return self._access_token

        if not self.validate_params(callback_params):
            raise AuthenticationError("Invalid HMAC: Possibly malicious login")

        code = callback_params.get("code")

        token_url = f"https://{self._shop_domain}/admin/oauth/access_token"
        token_params = {
            "client_id": self._api_key,
            "client_secret": self._secret_key,
            "code": code,
        }

        request = Request(
            token_url,
            data=urlencode(token_params).encode("utf-8")
        )

        try:
            response = urlopen(request)
            response_data = json.loads(response.read().decode("utf-8"))

            self._access_token = response_data.get("access_token")
            self._scopes = response_data.get("scope")

            return self._access_token
        except HTTPError as e:
            raise AuthenticationError(f"Token exchange failed: {e}")

    @classmethod
    def validate_params(cls, params):
        """Validate OAuth callback parameters.

        Checks both HMAC signature and timestamp freshness.

        Args:
            params: Dictionary of callback parameters

        Returns:
            True if parameters are valid, False otherwise
        """
        one_day_seconds = 24 * 60 * 60
        timestamp = int(params.get("timestamp", 0))

        if timestamp < time.time() - one_day_seconds:
            return False

        return cls.validate_hmac(params)

    @classmethod
    def validate_hmac(cls, params):
        """Validate the HMAC signature of OAuth callback parameters.

        Args:
            params: Dictionary containing 'hmac' and other parameters

        Returns:
            True if HMAC is valid, False otherwise
        """
        if "hmac" not in params:
            return False

        calculated = cls.calculate_hmac(params).encode("utf-8")
        provided = params["hmac"].encode("utf-8")

        return hmac.compare_digest(calculated, provided)

    @classmethod
    def calculate_hmac(cls, params):
        """Calculate HMAC signature for parameters.

        Args:
            params: Dictionary of parameters (hmac key is excluded)

        Returns:
            Hex-encoded HMAC-SHA256 signature
        """
        encoded_string = cls._encode_params_for_signature(params)
        signature = hmac.new(
            cls._secret_key.encode("utf-8"),
            encoded_string.encode("utf-8"),
            sha256
        )
        return signature.hexdigest()

    @classmethod
    def _encode_params_for_signature(cls, params):
        """Encode parameters for HMAC signing.

        Follows Shopify's OAuth signature requirements:
        - Excludes 'hmac' parameter
        - Handles array parameters (foo[]=1&foo[]=2 -> foo=["1", "2"])
        - Percent-encodes delimiters to prevent tampering
        - Sorts parameters alphabetically
        """
        pairs = []

        for key, value in params.items():
            if key == "hmac":
                continue

            k = str(key)
            v = value

            if k.endswith("[]"):
                k = k[:-2]
                v = json.dumps([str(x) for x in v])
            else:
                v = str(v)

            k = k.replace("%", "%25").replace("=", "%3D")
            v = v.replace("%", "%25")

            pair = f"{k}={v}".replace("&", "%26")
            pairs.append(pair)

        return "&".join(sorted(pairs))

    @classmethod
    def _normalize_shop_url(cls, url):
        """Normalize a shop URL to just the domain.

        Handles various input formats:
        - Full URL: https://shop.myshopify.com/path
        - Domain: shop.myshopify.com
        - Subdomain only: shop

        Returns:
            Normalized domain like "shop.myshopify.com"
        """
        if not url or not str(url).strip():
            return None

        url = str(url).strip()

        url = re.sub(r"^https?://", "", url)

        parsed = urlparse(f"https://{url}")
        hostname = parsed.hostname

        if hostname is None:
            return None

        dot_index = hostname.find(".")
        if dot_index != -1:
            subdomain = hostname[:dot_index]
        else:
            subdomain = hostname

        if not subdomain:
            return None

        domain = f"{subdomain}.{cls._domain_suffix}"

        if cls._port:
            domain = f"{domain}:{cls._port}"

        return domain
