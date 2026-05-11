"""Order resource for Shopify API."""

from ..resource import ResourceBase
from .metafield import Metafield
from .event import Event
from .transaction import Transaction
from .fulfillment import Fulfillment


class Order(ResourceBase):
    """Represents a Shopify order.

    Orders contain information about purchases made by customers.
    """

    _resource_name = "order"
    _resource_name_plural = "orders"
    _prefix_path = None

    @property
    def order_number(self):
        """The order number displayed to the customer."""
        return self._attributes.get("order_number")

    @property
    def name(self):
        """The order name (e.g., #1001)."""
        return self._attributes.get("name")

    @property
    def email(self):
        """The customer's email address."""
        return self._attributes.get("email")

    @property
    def phone(self):
        """The customer's phone number."""
        return self._attributes.get("phone")

    @property
    def total_price(self):
        """The total price of the order."""
        return self._attributes.get("total_price")

    @property
    def subtotal_price(self):
        """The subtotal (before shipping and taxes)."""
        return self._attributes.get("subtotal_price")

    @property
    def total_tax(self):
        """The total tax amount."""
        return self._attributes.get("total_tax")

    @property
    def total_discounts(self):
        """The total discounts applied."""
        return self._attributes.get("total_discounts")

    @property
    def currency(self):
        """The order currency."""
        return self._attributes.get("currency")

    @property
    def financial_status(self):
        """The financial status (pending, paid, refunded, etc.)."""
        return self._attributes.get("financial_status")

    @property
    def fulfillment_status(self):
        """The fulfillment status (fulfilled, partial, null)."""
        return self._attributes.get("fulfillment_status")

    @property
    def customer(self):
        """The customer who placed the order."""
        return self._attributes.get("customer")

    @property
    def shipping_address(self):
        """The shipping address."""
        return self._attributes.get("shipping_address")

    @property
    def billing_address(self):
        """The billing address."""
        return self._attributes.get("billing_address")

    @property
    def line_items(self):
        """The line items in the order."""
        return self._attributes.get("line_items", [])

    @property
    def note(self):
        """Notes about the order."""
        return self._attributes.get("note")

    @property
    def tags(self):
        """Tags associated with the order."""
        return self._attributes.get("tags")

    @property
    def cancelled_at(self):
        """When the order was cancelled."""
        return self._attributes.get("cancelled_at")

    @property
    def closed_at(self):
        """When the order was closed."""
        return self._attributes.get("closed_at")

    @property
    def created_at(self):
        """When the order was created."""
        return self._attributes.get("created_at")

    @property
    def updated_at(self):
        """When the order was last updated."""
        return self._attributes.get("updated_at")

    def close(self):
        """Close this order.

        Returns:
            Updated order data
        """
        data = self._custom_post("close")
        if "order" in data:
            self._attributes.update(data["order"])
        return self

    def open(self):
        """Reopen this order.

        Returns:
            Updated order data
        """
        data = self._custom_post("open")
        if "order" in data:
            self._attributes.update(data["order"])
        return self

    def cancel(self, reason=None, email=True, **kwargs):
        """Cancel this order.

        Args:
            reason: Cancellation reason
            email: Whether to notify the customer
            **kwargs: Additional cancellation options

        Returns:
            Updated order data
        """
        body = {"email": email}
        if reason:
            body["reason"] = reason
        body.update(kwargs)

        data = self._custom_post("cancel", body)
        if "order" in data:
            self._attributes.update(data["order"])
        return self

    def transactions(self, **kwargs):
        """Get transactions for this order.

        Returns:
            List of Transaction instances
        """
        if not self.id:
            return []
        return Transaction.find(order_id=self.id, **kwargs)

    def capture(self, amount=None):
        """Capture payment for this order.

        Args:
            amount: Amount to capture (captures full amount if not specified)

        Returns:
            The created Transaction instance
        """
        transaction = Transaction(
            {"kind": "capture", "amount": amount or self.total_price},
            {"order_id": self.id}
        )
        transaction.save()
        return transaction

    def fulfillments(self, **kwargs):
        """Get fulfillments for this order.

        Returns:
            List of Fulfillment instances
        """
        if not self.id:
            return []
        return Fulfillment.find(order_id=self.id, **kwargs)

    def metafields(self, **kwargs):
        """Get metafields for this order.

        Returns:
            List of Metafield instances
        """
        if not self.id:
            return []
        return Metafield.find(order_id=self.id, **kwargs)

    def events(self, **kwargs):
        """Get events for this order.

        Returns:
            List of Event instances
        """
        if not self.id:
            return []
        return Event.find(order_id=self.id, **kwargs)
