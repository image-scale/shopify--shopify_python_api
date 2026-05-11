"""Transaction resource for Shopify API."""

from ..resource import ResourceBase


class Transaction(ResourceBase):
    """Represents a Shopify transaction.

    Transactions record payments, refunds, and other financial operations.
    """

    _resource_name = "transaction"
    _resource_name_plural = "transactions"
    _prefix_path = "/orders/$order_id"

    @property
    def kind(self):
        """The transaction type (sale, capture, refund, etc.)."""
        return self._attributes.get("kind")

    @property
    def status(self):
        """The transaction status."""
        return self._attributes.get("status")

    @property
    def amount(self):
        """The transaction amount."""
        return self._attributes.get("amount")

    @property
    def currency(self):
        """The transaction currency."""
        return self._attributes.get("currency")

    @property
    def gateway(self):
        """The payment gateway used."""
        return self._attributes.get("gateway")

    @property
    def authorization(self):
        """The authorization code."""
        return self._attributes.get("authorization")

    @property
    def created_at(self):
        """When the transaction was created."""
        return self._attributes.get("created_at")

    @property
    def error_code(self):
        """Error code if the transaction failed."""
        return self._attributes.get("error_code")

    @property
    def message(self):
        """Transaction message or error message."""
        return self._attributes.get("message")

    @property
    def parent_id(self):
        """The parent transaction ID."""
        return self._attributes.get("parent_id")
