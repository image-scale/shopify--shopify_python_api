"""Shopify API Python Library.

A Python library for accessing the Shopify Admin API.
"""

from .session import ShopSession, AuthenticationError
from .resource import ResourceBase, ResourceError, ResourceNotFound
from .version import (
    Version,
    Release,
    UnstableVersion,
    VersionRegistry,
    VersionFormatError,
    VersionNotFoundError,
)
from .scopes import ScopeSet, ScopeFormatError
from .resources import (
    Shop, Metafield, Event, Product, Variant, Image,
    Customer, Order, Transaction, Fulfillment
)
from .graphql import GraphQLClient, GraphQLError
from .pagination import PaginatedCollection, PageIterator

__version__ = "1.0.0"

__all__ = [
    "ShopSession",
    "AuthenticationError",
    "ResourceBase",
    "ResourceError",
    "ResourceNotFound",
    "Version",
    "Release",
    "UnstableVersion",
    "VersionRegistry",
    "VersionFormatError",
    "VersionNotFoundError",
    "ScopeSet",
    "ScopeFormatError",
    "Shop",
    "Metafield",
    "Event",
    "Product",
    "Variant",
    "Image",
    "Customer",
    "Order",
    "Transaction",
    "Fulfillment",
    "GraphQLClient",
    "GraphQLError",
    "PaginatedCollection",
    "PageIterator",
    "__version__",
]
