"""Metafield resource for Shopify API."""

from ..resource import ResourceBase


class Metafield(ResourceBase):
    """Represents a Shopify metafield.

    Metafields allow you to attach additional information to resources
    like shops, products, customers, and orders.
    """

    _resource_name = "metafield"
    _resource_name_plural = "metafields"
    _prefix_path = None

    def __init__(self, attributes=None, prefix_options=None):
        """Initialize a metafield.

        Args:
            attributes: Dict with keys like namespace, key, value, value_type
            prefix_options: Options for nested resource URL prefix
        """
        super().__init__(attributes, prefix_options)

    @property
    def namespace(self):
        """The metafield namespace."""
        return self._attributes.get("namespace")

    @property
    def key(self):
        """The metafield key within the namespace."""
        return self._attributes.get("key")

    @property
    def value(self):
        """The metafield value."""
        return self._attributes.get("value")

    @property
    def value_type(self):
        """The metafield value type."""
        return self._attributes.get("value_type") or self._attributes.get("type")

    @classmethod
    def find_for_resource(cls, resource_type, resource_id, **kwargs):
        """Find metafields for a specific resource.

        Args:
            resource_type: The resource type (e.g., "products", "customers")
            resource_id: The resource ID

        Returns:
            List of Metafield instances
        """
        prefix_options = {"resource": resource_type, "resource_id": resource_id}
        return cls.find(**prefix_options, **kwargs)
