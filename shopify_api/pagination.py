"""Paginated collection support for Shopify API."""


class PaginatedCollection(list):
    """A collection that supports cursor-based pagination.

    Shopify uses Link headers for cursor-based pagination. This class
    wraps a list of resources and provides methods to navigate pages.
    """

    def __init__(self, items=None, resource_class=None, next_url=None, previous_url=None):
        """Initialize a paginated collection.

        Args:
            items: List of resource instances
            resource_class: The resource class for making additional requests
            next_url: URL for the next page
            previous_url: URL for the previous page
        """
        super().__init__(items or [])
        self._resource_class = resource_class
        self._next_url = next_url
        self._previous_url = previous_url
        self._cached_next = None
        self._cached_previous = None

    @property
    def next_page_url(self):
        """URL for fetching the next page."""
        return self._next_url

    @property
    def previous_page_url(self):
        """URL for fetching the previous page."""
        return self._previous_url

    def has_next_page(self):
        """Check if there is a next page.

        Returns:
            True if there are more pages after this one
        """
        return bool(self._next_url)

    def has_previous_page(self):
        """Check if there is a previous page.

        Returns:
            True if there are pages before this one
        """
        return bool(self._previous_url)

    def next_page(self, no_cache=False):
        """Fetch the next page of results.

        Args:
            no_cache: If True, don't cache the result

        Returns:
            A new PaginatedCollection with the next page's items

        Raises:
            IndexError: If there is no next page
        """
        if self._cached_next and not no_cache:
            return self._cached_next

        if not self.has_next_page():
            raise IndexError("No next page")

        items = self._resource_class.find(from_=self._next_url)

        if isinstance(items, PaginatedCollection):
            result = items
        else:
            result = PaginatedCollection(items, self._resource_class)

        if not no_cache:
            self._cached_next = result
            result._cached_previous = self

        return result

    def previous_page(self, no_cache=False):
        """Fetch the previous page of results.

        Args:
            no_cache: If True, don't cache the result

        Returns:
            A new PaginatedCollection with the previous page's items

        Raises:
            IndexError: If there is no previous page
        """
        if self._cached_previous and not no_cache:
            return self._cached_previous

        if not self.has_previous_page():
            raise IndexError("No previous page")

        items = self._resource_class.find(from_=self._previous_url)

        if isinstance(items, PaginatedCollection):
            result = items
        else:
            result = PaginatedCollection(items, self._resource_class)

        if not no_cache:
            self._cached_previous = result
            result._cached_next = self

        return result

    @classmethod
    def from_response(cls, items, resource_class, response_headers):
        """Create a paginated collection from API response headers.

        Args:
            items: List of resource instances
            resource_class: The resource class
            response_headers: HTTP response headers dict

        Returns:
            A PaginatedCollection instance
        """
        next_url = None
        previous_url = None

        link_header = response_headers.get("Link") or response_headers.get("link")
        if link_header:
            pagination = cls._parse_link_header(link_header)
            next_url = pagination.get("next")
            previous_url = pagination.get("previous")

        return cls(items, resource_class, next_url, previous_url)

    @staticmethod
    def _parse_link_header(link_header):
        """Parse the Link header into a dict of rel -> url.

        Args:
            link_header: The Link header value

        Returns:
            Dict mapping rel names to URLs
        """
        result = {}

        for part in link_header.split(", "):
            if "; " not in part:
                continue

            url_part, rel_part = part.split("; ", 1)
            url = url_part.strip("<>")

            if 'rel="' in rel_part:
                rel = rel_part.split('rel="')[1].rstrip('"')
                result[rel] = url

        return result


class PageIterator:
    """Iterator for efficiently traversing paginated collections.

    This iterator fetches pages one at a time and doesn't keep
    previous pages in memory, making it more memory efficient
    for large datasets.
    """

    def __init__(self, collection):
        """Initialize the page iterator.

        Args:
            collection: A PaginatedCollection to iterate over
        """
        if not isinstance(collection, PaginatedCollection):
            raise TypeError("PageIterator requires a PaginatedCollection")
        self._collection = collection

    def __iter__(self):
        """Iterate over pages, yielding one page at a time."""
        current = self._collection
        while True:
            yield current
            try:
                current = current.next_page(no_cache=True)
            except IndexError:
                return
