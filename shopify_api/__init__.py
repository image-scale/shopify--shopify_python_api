"""Shopify API Python Library.

A Python library for accessing the Shopify Admin API.
"""

from .session import ShopSession, AuthenticationError
from .resource import ResourceBase
from .version import (
    Version,
    Release,
    UnstableVersion,
    VersionRegistry,
    VersionFormatError,
    VersionNotFoundError,
)

__version__ = "1.0.0"

__all__ = [
    "ShopSession",
    "AuthenticationError",
    "ResourceBase",
    "Version",
    "Release",
    "UnstableVersion",
    "VersionRegistry",
    "VersionFormatError",
    "VersionNotFoundError",
    "__version__",
]
