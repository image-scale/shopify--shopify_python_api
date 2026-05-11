"""Shopify API Python Library.

A Python library for accessing the Shopify Admin API.
"""

from .session import ShopSession, AuthenticationError
from .resource import ResourceBase

__version__ = "1.0.0"

__all__ = [
    "ShopSession",
    "AuthenticationError",
    "ResourceBase",
    "__version__",
]
