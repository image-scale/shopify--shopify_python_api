"""Tests for API version management."""

import unittest

from shopify_api import (
    Version,
    Release,
    UnstableVersion,
    VersionRegistry,
    VersionFormatError,
    VersionNotFoundError,
)


class TestReleaseVersion(unittest.TestCase):
    """Test stable release versions."""

    def test_create_release_with_valid_format(self):
        version = Release("2024-07")
        self.assertEqual("2024-07", version.name)

    def test_release_numeric_version(self):
        version = Release("2024-07")
        self.assertEqual(202407, version.numeric_version)

    def test_release_is_stable(self):
        version = Release("2024-07")
        self.assertTrue(version.stable)

    def test_release_api_path(self):
        version = Release("2024-07")
        path = version.api_path("https://shop.myshopify.com")
        self.assertEqual("https://shop.myshopify.com/admin/api/2024-07", path)

    def test_release_invalid_format_raises_error(self):
        with self.assertRaises(VersionFormatError):
            Release("invalid-version")

    def test_release_invalid_format_missing_hyphen(self):
        with self.assertRaises(VersionFormatError):
            Release("202407")

    def test_release_invalid_format_extra_parts(self):
        with self.assertRaises(VersionFormatError):
            Release("2024-07-01")

    def test_release_equality(self):
        v1 = Release("2024-07")
        v2 = Release("2024-07")
        self.assertEqual(v1, v2)

    def test_release_inequality(self):
        v1 = Release("2024-07")
        v2 = Release("2024-01")
        self.assertNotEqual(v1, v2)

    def test_release_repr(self):
        version = Release("2024-07")
        self.assertIn("2024-07", repr(version))


class TestUnstableVersion(unittest.TestCase):
    """Test unstable/development version."""

    def test_unstable_name(self):
        version = UnstableVersion()
        self.assertEqual("unstable", version.name)

    def test_unstable_numeric_version_is_high(self):
        version = UnstableVersion()
        self.assertEqual(9000000, version.numeric_version)

    def test_unstable_is_not_stable(self):
        version = UnstableVersion()
        self.assertFalse(version.stable)

    def test_unstable_api_path(self):
        version = UnstableVersion()
        path = version.api_path("https://shop.myshopify.com")
        self.assertEqual("https://shop.myshopify.com/admin/api/unstable", path)

    def test_unstable_compares_higher_than_releases(self):
        unstable = UnstableVersion()
        release = Release("2024-07")
        self.assertGreater(unstable.numeric_version, release.numeric_version)


class TestVersionRegistry(unittest.TestCase):
    """Test version registration and lookup."""

    def setUp(self):
        VersionRegistry.clear()

    def tearDown(self):
        VersionRegistry.register_standard_versions()

    def test_register_and_get_version(self):
        version = Release("2024-07")
        VersionRegistry.register(version)

        retrieved = VersionRegistry.get("2024-07")
        self.assertEqual(version, retrieved)

    def test_get_nonexistent_returns_none(self):
        result = VersionRegistry.get("2099-01")
        self.assertIsNone(result)

    def test_coerce_registered_version(self):
        version = Release("2024-07")
        VersionRegistry.register(version)

        coerced = VersionRegistry.coerce_to_version("2024-07")
        self.assertIs(version, coerced)

    def test_coerce_creates_dynamic_release(self):
        coerced = VersionRegistry.coerce_to_version("2030-01")
        self.assertIsInstance(coerced, Release)
        self.assertEqual("2030-01", coerced.name)

    def test_coerce_invalid_format_raises_error(self):
        with self.assertRaises(VersionNotFoundError):
            VersionRegistry.coerce_to_version("invalid-version")

    def test_coerce_partial_version_raises_error(self):
        with self.assertRaises(VersionNotFoundError):
            VersionRegistry.coerce_to_version("2024")

    def test_clear_removes_all_versions(self):
        VersionRegistry.register(Release("2024-07"))
        VersionRegistry.clear()
        self.assertIsNone(VersionRegistry.get("2024-07"))


class TestStandardVersions(unittest.TestCase):
    """Test pre-registered standard versions."""

    def test_unstable_is_registered(self):
        version = VersionRegistry.get("unstable")
        self.assertIsNotNone(version)
        self.assertIsInstance(version, UnstableVersion)

    def test_2024_07_is_registered(self):
        version = VersionRegistry.get("2024-07")
        self.assertIsNotNone(version)
        self.assertIsInstance(version, Release)

    def test_2024_01_is_registered(self):
        version = VersionRegistry.get("2024-01")
        self.assertIsNotNone(version)

    def test_2023_10_is_registered(self):
        version = VersionRegistry.get("2023-10")
        self.assertIsNotNone(version)

    def test_coerce_unstable(self):
        version = VersionRegistry.coerce_to_version("unstable")
        self.assertIsInstance(version, UnstableVersion)


class TestVersionComparison(unittest.TestCase):
    """Test version comparison operations."""

    def test_newer_version_has_higher_numeric(self):
        v1 = Release("2024-07")
        v2 = Release("2024-01")
        self.assertGreater(v1.numeric_version, v2.numeric_version)

    def test_same_version_equals(self):
        v1 = Release("2024-07")
        v2 = Release("2024-07")
        self.assertEqual(v1.numeric_version, v2.numeric_version)

    def test_version_not_equal_to_non_version(self):
        version = Release("2024-07")
        self.assertNotEqual(version, "2024-07")
        self.assertNotEqual(version, 202407)


if __name__ == "__main__":
    unittest.main()
