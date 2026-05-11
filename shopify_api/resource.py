"""Resource base class for Shopify API resources."""

import json
import threading
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen
from urllib.error import HTTPError


class ResourceError(Exception):
    """Base exception for resource errors."""
    pass


class ResourceNotFound(ResourceError):
    """Raised when a resource is not found."""
    pass


class ResourceBase:
    """Base class for Shopify API resources.

    Provides ActiveResource-style CRUD operations and manages
    thread-local session state for API connections.
    """

    _thread_local = threading.local()
    _session = None
    _site = None
    _headers = {}
    _response = None

    _resource_name = None
    _resource_name_plural = None
    _prefix_path = None

    def __init__(self, attributes=None, prefix_options=None):
        """Initialize a resource instance.

        Args:
            attributes: Dictionary of resource attributes
            prefix_options: Options for URL prefix (e.g., order_id for nested resources)
        """
        self._attributes = attributes or {}
        self._prefix_options = prefix_options or {}
        self._persisted = False

    @property
    def id(self):
        """The resource ID."""
        return self._attributes.get("id")

    @id.setter
    def id(self, value):
        """Set the resource ID."""
        self._attributes["id"] = value

    @property
    def attributes(self):
        """All resource attributes."""
        return self._attributes

    def __getattr__(self, name):
        """Access attributes as properties."""
        if name.startswith("_"):
            raise AttributeError(name)
        if name in self._attributes:
            return self._attributes[name]
        raise AttributeError(f"'{type(self).__name__}' has no attribute '{name}'")

    def __setattr__(self, name, value):
        """Set attributes as properties."""
        if name.startswith("_"):
            object.__setattr__(self, name, value)
        else:
            self._attributes[name] = value

    def is_new(self):
        """Check if this resource has been saved."""
        return not self.id

    @classmethod
    def get_session_state(cls):
        """Capture current session state for later restoration."""
        return {
            "session": getattr(cls._thread_local, "session", cls._session),
            "site": getattr(cls._thread_local, "site", cls._site),
            "headers": getattr(cls._thread_local, "headers", cls._headers.copy()),
        }

    @classmethod
    def restore_session_state(cls, state):
        """Restore a previously captured session state."""
        cls._thread_local.session = state.get("session")
        cls._thread_local.site = state.get("site")
        cls._thread_local.headers = state.get("headers", {})
        cls._session = state.get("session")
        cls._site = state.get("site")
        cls._headers = state.get("headers", {})

    @classmethod
    def activate_session(cls, session):
        """Activate a session for API requests.

        Args:
            session: A ShopSession instance
        """
        cls._thread_local.session = session
        cls._session = session

        if session and session.site:
            cls._thread_local.site = session.site
            cls._site = session.site

            cls._thread_local.headers = {
                "X-Shopify-Access-Token": session.token
            }
            cls._headers = cls._thread_local.headers.copy()

    @classmethod
    def set_active_session(cls, session):
        """Alias for activate_session for backward compatibility."""
        cls.activate_session(session)

    @classmethod
    def clear_session(cls):
        """Clear the current session."""
        cls._thread_local.session = None
        cls._thread_local.site = None
        cls._thread_local.headers = {}
        cls._session = None
        cls._site = None
        cls._headers = {}

    @classmethod
    def get_site(cls):
        """Get the current API site URL."""
        return getattr(cls._thread_local, "site", cls._site)

    @classmethod
    def site(cls):
        """Get the current API site URL."""
        return cls.get_site()

    @classmethod
    def get_headers(cls):
        """Get the current request headers."""
        local_headers = getattr(cls._thread_local, "headers", None)
        if local_headers is not None:
            return local_headers.copy()
        return cls._headers.copy()

    @classmethod
    def headers(cls):
        """Get the current request headers."""
        return cls.get_headers()

    @classmethod
    def _singular_name(cls):
        """Get the singular resource name."""
        if cls._resource_name:
            return cls._resource_name
        name = cls.__name__
        return name[0].lower() + name[1:]

    @classmethod
    def _plural_name(cls):
        """Get the plural resource name."""
        if cls._resource_name_plural:
            return cls._resource_name_plural
        return cls._singular_name() + "s"

    @classmethod
    def _prefix(cls, options=None):
        """Get the URL prefix for this resource type.

        Args:
            options: Prefix options for nested resources

        Returns:
            URL prefix string
        """
        site = cls.get_site()
        if not site:
            raise ResourceError("No active session")

        if cls._prefix_path and options:
            prefix = cls._prefix_path
            for key, value in options.items():
                placeholder = f"${key}"
                prefix = prefix.replace(placeholder, str(value))
            return f"{site}{prefix}"

        return site

    @classmethod
    def _collection_path(cls, prefix_options=None, query_params=None):
        """Build the collection URL path.

        Args:
            prefix_options: Options for URL prefix
            query_params: Query parameters to append

        Returns:
            Full URL for the collection
        """
        base = cls._prefix(prefix_options)
        path = f"{base}/{cls._plural_name()}.json"

        if query_params:
            filtered = {k: v for k, v in query_params.items() if v is not None}
            if filtered:
                path = f"{path}?{urlencode(filtered)}"

        return path

    @classmethod
    def _element_path(cls, id_, prefix_options=None):
        """Build the element URL path.

        Args:
            id_: The resource ID
            prefix_options: Options for URL prefix

        Returns:
            Full URL for the element
        """
        base = cls._prefix(prefix_options)
        return f"{base}/{cls._plural_name()}/{id_}.json"

    @classmethod
    def _custom_method_path(cls, method_name, id_=None, prefix_options=None):
        """Build URL path for custom methods.

        Args:
            method_name: The custom method name
            id_: Optional resource ID
            prefix_options: Options for URL prefix

        Returns:
            Full URL for the custom method
        """
        base = cls._prefix(prefix_options)
        if id_:
            return f"{base}/{cls._plural_name()}/{id_}/{method_name}.json"
        return f"{base}/{cls._plural_name()}/{method_name}.json"

    @classmethod
    def _make_request(cls, method, url, body=None):
        """Make an HTTP request.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            url: Request URL
            body: Optional request body (dict for JSON)

        Returns:
            Response data as dict

        Raises:
            ResourceNotFound: If resource not found (404)
            ResourceError: For other HTTP errors
        """
        headers = cls.get_headers()
        headers["Content-Type"] = "application/json"
        headers["Accept"] = "application/json"

        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")

        request = Request(url, data=data, headers=headers, method=method)

        try:
            response = urlopen(request)
            cls._response = response

            content = response.read().decode("utf-8")
            if content:
                return json.loads(content)
            return {}

        except HTTPError as e:
            cls._response = e
            if e.code == 404:
                raise ResourceNotFound(f"Resource not found: {url}")
            raise ResourceError(f"HTTP {e.code}: {e.reason}")

    @classmethod
    def find(cls, id_=None, from_=None, **kwargs):
        """Find resources.

        Args:
            id_: Resource ID to find a single resource
            from_: URL to fetch from (for pagination)
            **kwargs: Query parameters or prefix options

        Returns:
            Single resource instance or list of resources
        """
        prefix_options = {}
        query_params = {}

        for key, value in kwargs.items():
            if key.endswith("_id"):
                prefix_options[key] = value
            else:
                query_params[key] = value

        if from_:
            url = from_
        elif id_:
            url = cls._element_path(id_, prefix_options)
        else:
            url = cls._collection_path(prefix_options, query_params)

        data = cls._make_request("GET", url)

        if id_:
            singular = cls._singular_name()
            if singular in data:
                resource = cls(data[singular], prefix_options)
                resource._persisted = True
                return resource
            return cls(data, prefix_options)
        else:
            plural = cls._plural_name()
            if plural in data:
                return [
                    cls._create_instance(item, prefix_options)
                    for item in data[plural]
                ]
            return []

    @classmethod
    def _create_instance(cls, attributes, prefix_options=None):
        """Create a resource instance from attributes."""
        resource = cls(attributes, prefix_options)
        resource._persisted = True
        return resource

    @classmethod
    def count(cls, **kwargs):
        """Get the count of resources.

        Args:
            **kwargs: Query parameters

        Returns:
            Integer count
        """
        prefix_options = {}
        query_params = {}

        for key, value in kwargs.items():
            if key.endswith("_id"):
                prefix_options[key] = value
            else:
                query_params[key] = value

        url = cls._custom_method_path("count", prefix_options=prefix_options)
        if query_params:
            url = f"{url}?{urlencode(query_params)}"

        data = cls._make_request("GET", url)
        return data.get("count", 0)

    @classmethod
    def exists(cls, id_, **kwargs):
        """Check if a resource exists.

        Args:
            id_: Resource ID
            **kwargs: Prefix options

        Returns:
            True if resource exists
        """
        try:
            cls.find(id_, **kwargs)
            return True
        except ResourceNotFound:
            return False

    def save(self):
        """Save this resource.

        Creates a new resource (POST) if no ID, updates (PUT) if ID exists.

        Returns:
            True if successful
        """
        singular = self._singular_name()
        body = {singular: self._attributes}

        if self.id:
            url = self._element_path(self.id, self._prefix_options)
            data = self._make_request("PUT", url, body)
        else:
            url = self._collection_path(self._prefix_options)
            data = self._make_request("POST", url, body)

        if singular in data:
            self._attributes.update(data[singular])

        self._persisted = True
        return True

    def destroy(self):
        """Delete this resource.

        Returns:
            True if successful
        """
        if not self.id:
            raise ResourceError("Cannot delete unsaved resource")

        url = self._element_path(self.id, self._prefix_options)
        self._make_request("DELETE", url)
        return True

    def reload(self):
        """Reload this resource from the server.

        Returns:
            Self with updated attributes
        """
        if not self.id:
            raise ResourceError("Cannot reload unsaved resource")

        fresh = self.find(self.id, **self._prefix_options)
        self._attributes = fresh._attributes
        return self

    def _custom_post(self, method_name, body=None):
        """Make a custom POST request.

        Args:
            method_name: The method name
            body: Optional request body

        Returns:
            Response data
        """
        url = self._custom_method_path(method_name, self.id, self._prefix_options)
        return self._make_request("POST", url, body)

    def _custom_get(self, method_name):
        """Make a custom GET request.

        Args:
            method_name: The method name

        Returns:
            Response data
        """
        url = self._custom_method_path(method_name, self.id, self._prefix_options)
        return self._make_request("GET", url)

    def to_dict(self):
        """Convert resource to dictionary."""
        return self._attributes.copy()

    def __repr__(self):
        return f"<{self.__class__.__name__} {self._attributes}>"
