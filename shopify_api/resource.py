"""Resource base class for Shopify API resources."""

import threading


class ResourceBase:
    """Base class for Shopify API resources.

    Manages thread-local session state for API connections.
    """

    _thread_local = threading.local()
    _session = None
    _site = None
    _headers = {}

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
    def set_active_session(cls, session):
        """Activate a session for API requests."""
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
    def get_headers(cls):
        """Get the current request headers."""
        local_headers = getattr(cls._thread_local, "headers", None)
        if local_headers is not None:
            return local_headers
        return cls._headers.copy()
