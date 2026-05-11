"""API version management for Shopify API."""

import re


class VersionFormatError(Exception):
    """Raised when a version string has an invalid format."""
    pass


class VersionNotFoundError(Exception):
    """Raised when a version cannot be resolved."""
    pass


class Version:
    """Base class for Shopify API versions.

    API versions control which endpoint paths and behaviors are used.
    """

    _API_PREFIX = "/admin/api"

    def __init__(self):
        self._name = None
        self._numeric = None
        self._path_suffix = None

    @property
    def name(self):
        """The version string identifier."""
        return self._name

    @property
    def numeric_version(self):
        """Numeric version for comparison."""
        return self._numeric

    @property
    def stable(self):
        """Whether this is a stable release version."""
        raise NotImplementedError

    def api_path(self, base_url):
        """Generate the full API URL path.

        Args:
            base_url: Base URL like "https://shop.myshopify.com"

        Returns:
            Full API path like "https://shop.myshopify.com/admin/api/2024-07"
        """
        return f"{base_url}{self._API_PREFIX}/{self._path_suffix}"

    def __eq__(self, other):
        if not isinstance(other, Version):
            return False
        return self.numeric_version == other.numeric_version

    def __repr__(self):
        return f"<{self.__class__.__name__} {self._name}>"


class Release(Version):
    """A stable release version of the Shopify API.

    Release versions follow the YYYY-MM format (e.g., "2024-07").
    """

    VERSION_PATTERN = re.compile(r"^\d{4}-\d{2}$")

    def __init__(self, version_string):
        """Create a release version.

        Args:
            version_string: Version in YYYY-MM format (e.g., "2024-07")

        Raises:
            VersionFormatError: If version string is not in YYYY-MM format
        """
        super().__init__()

        if not self.VERSION_PATTERN.match(version_string):
            raise VersionFormatError(
                f"Invalid version format: '{version_string}'. Expected YYYY-MM format."
            )

        self._name = version_string
        self._numeric = int(version_string.replace("-", ""))
        self._path_suffix = version_string

    @property
    def stable(self):
        """Release versions are always stable."""
        return True


class UnstableVersion(Version):
    """The unstable/development version of the Shopify API.

    The unstable version may include breaking changes and
    should only be used for development and testing.
    """

    def __init__(self):
        super().__init__()
        self._name = "unstable"
        self._numeric = 9000000
        self._path_suffix = "unstable"

    @property
    def stable(self):
        """Unstable versions are not stable."""
        return False


class VersionRegistry:
    """Registry for known Shopify API versions.

    Provides version lookup and dynamic version creation.
    """

    _known_versions = {}

    @classmethod
    def register(cls, version):
        """Register a version for lookup.

        Args:
            version: A Version instance

        Returns:
            The registered version
        """
        cls._known_versions[version.name] = version
        return version

    @classmethod
    def get(cls, version_name):
        """Get a registered version by name.

        Args:
            version_name: The version string

        Returns:
            The version if found, None otherwise
        """
        return cls._known_versions.get(version_name)

    @classmethod
    def coerce_to_version(cls, version_string):
        """Resolve a version string to a Version object.

        First checks registered versions, then attempts to create
        a new Release version dynamically if the format is valid.

        Args:
            version_string: Version string like "2024-07" or "unstable"

        Returns:
            A Version instance

        Raises:
            VersionNotFoundError: If version cannot be resolved
        """
        existing = cls._known_versions.get(version_string)
        if existing:
            return existing

        if Release.VERSION_PATTERN.match(version_string):
            return Release(version_string)

        raise VersionNotFoundError(
            f"Cannot resolve version: '{version_string}'"
        )

    @classmethod
    def clear(cls):
        """Clear all registered versions."""
        cls._known_versions = {}

    @classmethod
    def register_standard_versions(cls):
        """Register commonly used Shopify API versions."""
        cls.register(UnstableVersion())

        standard_releases = [
            "2021-10",
            "2022-01",
            "2022-04",
            "2022-07",
            "2022-10",
            "2023-01",
            "2023-04",
            "2023-07",
            "2023-10",
            "2024-01",
            "2024-04",
            "2024-07",
            "2024-10",
        ]

        for version_str in standard_releases:
            cls.register(Release(version_str))


VersionRegistry.register_standard_versions()
