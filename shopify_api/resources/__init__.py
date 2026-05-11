"""Shopify API resources."""

from .shop import Shop
from .metafield import Metafield
from .event import Event
from .product import Product
from .variant import Variant
from .image import Image
from .customer import Customer
from .order import Order
from .transaction import Transaction
from .fulfillment import Fulfillment

__all__ = [
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
]
