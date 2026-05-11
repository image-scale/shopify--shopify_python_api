"""Variant resource for Shopify API."""

from ..resource import ResourceBase


class Variant(ResourceBase):
    """Represents a Shopify product variant.

    Variants are different versions of a product (e.g., different sizes or colors).
    """

    _resource_name = "variant"
    _resource_name_plural = "variants"
    _prefix_path = "/products/$product_id"

    @property
    def price(self):
        """The variant price."""
        return self._attributes.get("price")

    @price.setter
    def price(self, value):
        """Set the variant price."""
        self._attributes["price"] = value

    @property
    def sku(self):
        """The variant SKU."""
        return self._attributes.get("sku")

    @sku.setter
    def sku(self, value):
        """Set the variant SKU."""
        self._attributes["sku"] = value

    @property
    def inventory_quantity(self):
        """The variant inventory quantity."""
        return self._attributes.get("inventory_quantity", 0)

    @property
    def title(self):
        """The variant title."""
        return self._attributes.get("title")

    @property
    def option1(self):
        """First option value."""
        return self._attributes.get("option1")

    @property
    def option2(self):
        """Second option value."""
        return self._attributes.get("option2")

    @property
    def option3(self):
        """Third option value."""
        return self._attributes.get("option3")

    @property
    def product_id(self):
        """The parent product ID."""
        return self._attributes.get("product_id")

    @property
    def weight(self):
        """The variant weight."""
        return self._attributes.get("weight")

    @property
    def weight_unit(self):
        """The weight unit (kg, g, lb, oz)."""
        return self._attributes.get("weight_unit")

    @property
    def taxable(self):
        """Whether the variant is taxable."""
        return self._attributes.get("taxable", True)

    @property
    def barcode(self):
        """The variant barcode."""
        return self._attributes.get("barcode")
