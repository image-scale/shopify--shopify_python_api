"""Image resource for Shopify API."""

from ..resource import ResourceBase


class Image(ResourceBase):
    """Represents a Shopify product image.

    Images can be associated with products and have positions that determine
    display order.
    """

    _resource_name = "image"
    _resource_name_plural = "images"
    _prefix_path = "/products/$product_id"

    @property
    def src(self):
        """The image source URL."""
        return self._attributes.get("src")

    @src.setter
    def src(self, value):
        """Set the image source URL."""
        self._attributes["src"] = value

    @property
    def position(self):
        """The image position (display order)."""
        return self._attributes.get("position", 1)

    @position.setter
    def position(self, value):
        """Set the image position."""
        self._attributes["position"] = value

    @property
    def product_id(self):
        """The parent product ID."""
        return self._attributes.get("product_id")

    @property
    def width(self):
        """The image width in pixels."""
        return self._attributes.get("width")

    @property
    def height(self):
        """The image height in pixels."""
        return self._attributes.get("height")

    @property
    def alt(self):
        """The image alt text."""
        return self._attributes.get("alt")

    @alt.setter
    def alt(self, value):
        """Set the image alt text."""
        self._attributes["alt"] = value

    @property
    def variant_ids(self):
        """List of variant IDs this image is associated with."""
        return self._attributes.get("variant_ids", [])
