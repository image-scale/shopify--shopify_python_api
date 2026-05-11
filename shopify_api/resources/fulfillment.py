"""Fulfillment resource for Shopify API."""

from ..resource import ResourceBase


class Fulfillment(ResourceBase):
    """Represents a Shopify fulfillment.

    Fulfillments track the shipping and delivery of order items.
    """

    _resource_name = "fulfillment"
    _resource_name_plural = "fulfillments"
    _prefix_path = "/orders/$order_id"

    @property
    def status(self):
        """The fulfillment status."""
        return self._attributes.get("status")

    @property
    def tracking_number(self):
        """The tracking number."""
        return self._attributes.get("tracking_number")

    @property
    def tracking_numbers(self):
        """List of tracking numbers."""
        return self._attributes.get("tracking_numbers", [])

    @property
    def tracking_url(self):
        """The tracking URL."""
        return self._attributes.get("tracking_url")

    @property
    def tracking_urls(self):
        """List of tracking URLs."""
        return self._attributes.get("tracking_urls", [])

    @property
    def tracking_company(self):
        """The shipping carrier."""
        return self._attributes.get("tracking_company")

    @property
    def shipment_status(self):
        """The shipment status."""
        return self._attributes.get("shipment_status")

    @property
    def created_at(self):
        """When the fulfillment was created."""
        return self._attributes.get("created_at")

    @property
    def updated_at(self):
        """When the fulfillment was last updated."""
        return self._attributes.get("updated_at")

    @property
    def line_items(self):
        """The fulfilled line items."""
        return self._attributes.get("line_items", [])

    @property
    def order_id(self):
        """The parent order ID."""
        return self._attributes.get("order_id")

    def cancel(self):
        """Cancel this fulfillment.

        Returns:
            Updated fulfillment data
        """
        data = self._custom_post("cancel")
        if "fulfillment" in data:
            self._attributes.update(data["fulfillment"])
        return self

    def complete(self):
        """Mark this fulfillment as complete.

        Returns:
            Updated fulfillment data
        """
        data = self._custom_post("complete")
        if "fulfillment" in data:
            self._attributes.update(data["fulfillment"])
        return self

    def open(self):
        """Reopen this fulfillment.

        Returns:
            Updated fulfillment data
        """
        data = self._custom_post("open")
        if "fulfillment" in data:
            self._attributes.update(data["fulfillment"])
        return self
