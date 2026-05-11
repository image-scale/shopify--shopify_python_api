"""Shop resource for Shopify API."""

from ..resource import ResourceBase, ResourceError
from .metafield import Metafield
from .event import Event


class Shop(ResourceBase):
    """Represents a Shopify shop.

    The Shop resource contains information about the store,
    including its name, address, and configuration.
    """

    _resource_name = "shop"
    _resource_name_plural = "shops"

    @classmethod
    def current(cls):
        """Get the current shop.

        Returns:
            Shop instance with the current shop's information
        """
        site = cls.get_site()
        if not site:
            raise ResourceError("No active session")

        url = f"{site}/shop.json"
        data = cls._make_request("GET", url)

        if "shop" in data:
            shop = cls(data["shop"])
            shop._persisted = True
            return shop
        return cls(data)

    @property
    def name(self):
        """The shop name."""
        return self._attributes.get("name")

    @property
    def email(self):
        """The shop email address."""
        return self._attributes.get("email")

    @property
    def domain(self):
        """The shop's primary domain."""
        return self._attributes.get("domain")

    @property
    def myshopify_domain(self):
        """The shop's myshopify.com domain."""
        return self._attributes.get("myshopify_domain")

    @property
    def shop_owner(self):
        """The shop owner's name."""
        return self._attributes.get("shop_owner")

    @property
    def plan_name(self):
        """The shop's Shopify plan name."""
        return self._attributes.get("plan_name")

    @property
    def currency(self):
        """The shop's default currency."""
        return self._attributes.get("currency")

    @property
    def timezone(self):
        """The shop's timezone."""
        return self._attributes.get("timezone")

    @property
    def country(self):
        """The shop's country."""
        return self._attributes.get("country")

    @property
    def created_at(self):
        """When the shop was created."""
        return self._attributes.get("created_at")

    def metafields(self, **kwargs):
        """Get metafields for this shop.

        Returns:
            List of Metafield instances
        """
        return Metafield.find(**kwargs)

    def add_metafield(self, metafield):
        """Add a metafield to this shop.

        Args:
            metafield: Metafield instance to add

        Returns:
            The saved Metafield instance

        Raises:
            ValueError: If the shop hasn't been saved yet
        """
        if self.is_new():
            raise ValueError("You can only add metafields to a resource that has been saved")

        metafield.save()
        return metafield

    def events(self, **kwargs):
        """Get events for this shop.

        Returns:
            List of Event instances
        """
        return Event.find(**kwargs)
