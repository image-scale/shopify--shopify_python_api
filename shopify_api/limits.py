"""API call limit tracking for Shopify API."""

from .resource import ResourceBase


class LimitsError(Exception):
    """Error when accessing API limits."""
    pass


class Limits:
    """Track Shopify API call limits.

    Shopify uses a leaky bucket algorithm for rate limiting. Each response
    includes a header indicating how many API calls have been used and
    the total available in the bucket.

    The header format is: X-Shopify-Shop-Api-Call-Limit: used/total
    Example: "40/40" means 40 calls used out of 40 available.
    """

    LIMIT_HEADER = "X-Shopify-Shop-Api-Call-Limit"
    RETRY_HEADER = "Retry-After"

    @classmethod
    def _get_response(cls):
        """Get the last HTTP response."""
        response = ResourceBase._response
        if not response:
            raise LimitsError("No response available - make an API call first")
        return response

    @classmethod
    def _get_limit_header(cls):
        """Parse the API call limit header.

        Returns:
            Tuple of (used, limit) as integers

        Raises:
            LimitsError: If no limit header is found
        """
        response = cls._get_response()
        headers = getattr(response, "headers", {})

        header_value = None
        for key, value in headers.items():
            if key.lower() == cls.LIMIT_HEADER.lower():
                header_value = value
                break

        if not header_value:
            raise LimitsError("No API call limit header found")

        used_str, limit_str = header_value.split("/")
        return int(used_str), int(limit_str)

    @classmethod
    def credit_limit(cls):
        """Get the total API call limit (bucket size).

        Returns:
            Integer representing the maximum calls allowed
        """
        _, limit = cls._get_limit_header()
        return limit

    @classmethod
    def credit_used(cls):
        """Get the number of API calls used.

        Returns:
            Integer representing calls made in the current bucket
        """
        used, _ = cls._get_limit_header()
        return used

    @classmethod
    def credit_left(cls):
        """Get the number of API calls remaining.

        Returns:
            Integer representing available calls before hitting the limit
        """
        used, limit = cls._get_limit_header()
        return limit - used

    @classmethod
    def credit_maxed(cls):
        """Check if the API call limit has been reached.

        Returns:
            True if no more calls can be made without waiting
        """
        return cls.credit_left() <= 0

    @classmethod
    def retry_after(cls):
        """Get the retry delay when rate limited.

        Returns:
            Float seconds to wait, or None if not rate limited
        """
        response = cls._get_response()
        headers = getattr(response, "headers", {})

        for key, value in headers.items():
            if key.lower() == cls.RETRY_HEADER.lower():
                return float(value)

        return None
