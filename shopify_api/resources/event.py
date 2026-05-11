"""Event resource for Shopify API."""

from ..resource import ResourceBase


class Event(ResourceBase):
    """Represents a Shopify event.

    Events record activity that happens in a shop, such as changes
    to orders, products, and other resources.
    """

    _resource_name = "event"
    _resource_name_plural = "events"

    @property
    def subject_type(self):
        """The type of resource that triggered the event."""
        return self._attributes.get("subject_type")

    @property
    def subject_id(self):
        """The ID of the resource that triggered the event."""
        return self._attributes.get("subject_id")

    @property
    def verb(self):
        """The action that triggered the event (e.g., 'created', 'updated')."""
        return self._attributes.get("verb")

    @property
    def created_at(self):
        """When the event was created."""
        return self._attributes.get("created_at")

    @property
    def message(self):
        """Human-readable description of the event."""
        return self._attributes.get("message")

    @property
    def arguments(self):
        """Additional event arguments."""
        return self._attributes.get("arguments", [])

    @classmethod
    def find_for_resource(cls, resource_type, resource_id, **kwargs):
        """Find events for a specific resource.

        Args:
            resource_type: The resource type (e.g., "products", "orders")
            resource_id: The resource ID

        Returns:
            List of Event instances
        """
        prefix_options = {"resource": resource_type, "resource_id": resource_id}
        return cls.find(**prefix_options, **kwargs)
