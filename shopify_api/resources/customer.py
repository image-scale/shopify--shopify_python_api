"""Customer resource for Shopify API."""

from ..resource import ResourceBase
from .metafield import Metafield


class Customer(ResourceBase):
    """Represents a Shopify customer.

    Customers are people who have placed orders or created accounts.
    """

    _resource_name = "customer"
    _resource_name_plural = "customers"

    @property
    def first_name(self):
        """The customer's first name."""
        return self._attributes.get("first_name")

    @property
    def last_name(self):
        """The customer's last name."""
        return self._attributes.get("last_name")

    @property
    def email(self):
        """The customer's email address."""
        return self._attributes.get("email")

    @property
    def phone(self):
        """The customer's phone number."""
        return self._attributes.get("phone")

    @property
    def orders_count(self):
        """The number of orders placed by this customer."""
        return self._attributes.get("orders_count", 0)

    @property
    def total_spent(self):
        """The total amount spent by this customer."""
        return self._attributes.get("total_spent", "0.00")

    @property
    def verified_email(self):
        """Whether the customer's email is verified."""
        return self._attributes.get("verified_email", False)

    @property
    def accepts_marketing(self):
        """Whether the customer accepts marketing emails."""
        return self._attributes.get("accepts_marketing", False)

    @property
    def state(self):
        """The customer's account state (enabled, disabled, invited, declined)."""
        return self._attributes.get("state")

    @property
    def note(self):
        """Notes about the customer."""
        return self._attributes.get("note")

    @property
    def tags(self):
        """Tags associated with the customer."""
        return self._attributes.get("tags")

    @property
    def addresses(self):
        """The customer's addresses."""
        return self._attributes.get("addresses", [])

    @property
    def default_address(self):
        """The customer's default address."""
        return self._attributes.get("default_address")

    @property
    def created_at(self):
        """When the customer was created."""
        return self._attributes.get("created_at")

    @property
    def updated_at(self):
        """When the customer was last updated."""
        return self._attributes.get("updated_at")

    @classmethod
    def search(cls, query=None, **kwargs):
        """Search for customers.

        Args:
            query: Search query string
            **kwargs: Additional query parameters

        Returns:
            List of Customer instances matching the search
        """
        if query:
            kwargs["query"] = query

        url = cls._custom_method_path("search")
        if kwargs:
            from urllib.parse import urlencode
            url = f"{url}?{urlencode(kwargs)}"

        data = cls._make_request("GET", url)

        plural = cls._plural_name()
        if plural in data:
            return [cls._create_instance(item) for item in data[plural]]
        return []

    def orders(self, **kwargs):
        """Get orders for this customer.

        Returns:
            List of Order instances
        """
        from .order import Order
        if not self.id:
            return []
        return Order.find(customer_id=self.id, **kwargs)

    def metafields(self, **kwargs):
        """Get metafields for this customer.

        Returns:
            List of Metafield instances
        """
        if not self.id:
            return []
        return Metafield.find(customer_id=self.id, **kwargs)

    def add_metafield(self, metafield):
        """Add a metafield to this customer.

        Args:
            metafield: Metafield instance to add

        Returns:
            The saved Metafield instance
        """
        if self.is_new():
            raise ValueError("You can only add metafields to a saved customer")

        metafield._prefix_options = {"customer_id": self.id}
        metafield.save()
        return metafield

    def send_invite(self, invite_data=None):
        """Send an account invitation to the customer.

        Args:
            invite_data: Optional dict with invitation customization

        Returns:
            The invitation response data
        """
        body = {"customer_invite": invite_data or {}}
        data = self._custom_post("send_invite", body)
        return data.get("customer_invite", data)
