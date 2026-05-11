"""Product resource for Shopify API."""

from ..resource import ResourceBase
from .metafield import Metafield
from .event import Event
from .variant import Variant
from .image import Image


class Product(ResourceBase):
    """Represents a Shopify product.

    Products are the main items being sold in a store.
    """

    _resource_name = "product"
    _resource_name_plural = "products"

    @property
    def title(self):
        """The product title."""
        return self._attributes.get("title")

    @title.setter
    def title(self, value):
        """Set the product title."""
        self._attributes["title"] = value

    @property
    def body_html(self):
        """The product description in HTML."""
        return self._attributes.get("body_html")

    @body_html.setter
    def body_html(self, value):
        """Set the product description."""
        self._attributes["body_html"] = value

    @property
    def vendor(self):
        """The product vendor."""
        return self._attributes.get("vendor")

    @property
    def product_type(self):
        """The product type."""
        return self._attributes.get("product_type")

    @property
    def handle(self):
        """The product handle (URL slug)."""
        return self._attributes.get("handle")

    @property
    def tags(self):
        """The product tags."""
        return self._attributes.get("tags")

    @property
    def published_at(self):
        """When the product was published."""
        return self._attributes.get("published_at")

    @property
    def created_at(self):
        """When the product was created."""
        return self._attributes.get("created_at")

    @property
    def updated_at(self):
        """When the product was last updated."""
        return self._attributes.get("updated_at")

    @property
    def variants(self):
        """Get the product's variants.

        Returns:
            List of Variant instances
        """
        variants_data = self._attributes.get("variants", [])
        return [
            Variant(v, {"product_id": self.id})
            for v in variants_data
        ]

    @property
    def images(self):
        """Get the product's images.

        Returns:
            List of Image instances
        """
        images_data = self._attributes.get("images", [])
        return [
            Image(i, {"product_id": self.id})
            for i in images_data
        ]

    @property
    def options(self):
        """Get the product's options (e.g., Size, Color)."""
        return self._attributes.get("options", [])

    def price_range(self):
        """Calculate the price range for this product.

        Returns:
            A formatted price range string like "19.99 - 29.99"
            or a single price if all variants have the same price.
        """
        variants = self.variants
        if not variants:
            return "0.00"

        prices = []
        for variant in variants:
            price = variant.price
            if price is not None:
                try:
                    prices.append(float(price))
                except (ValueError, TypeError):
                    pass

        if not prices:
            return "0.00"

        min_price = min(prices)
        max_price = max(prices)

        fmt = "{:.2f}"

        if min_price == max_price:
            return fmt.format(min_price)

        return "{} - {}".format(fmt.format(min_price), fmt.format(max_price))

    def metafields(self, **kwargs):
        """Get metafields for this product.

        Returns:
            List of Metafield instances
        """
        if not self.id:
            return []
        return Metafield.find(product_id=self.id, **kwargs)

    def add_metafield(self, metafield):
        """Add a metafield to this product.

        Args:
            metafield: Metafield instance to add

        Returns:
            The saved Metafield instance

        Raises:
            ValueError: If the product hasn't been saved yet
        """
        if self.is_new():
            raise ValueError("You can only add metafields to a resource that has been saved")

        metafield._prefix_options = {"product_id": self.id}
        metafield.save()
        return metafield

    def add_variant(self, variant):
        """Add a variant to this product.

        Args:
            variant: Variant instance to add

        Returns:
            True if successful
        """
        variant._attributes["product_id"] = self.id
        variant._prefix_options = {"product_id": self.id}
        return variant.save()

    def events(self, **kwargs):
        """Get events for this product.

        Returns:
            List of Event instances
        """
        if not self.id:
            return []
        return Event.find(product_id=self.id, **kwargs)
