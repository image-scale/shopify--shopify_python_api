"""Tests for API access scope management."""

import unittest

from shopify_api import ScopeSet, ScopeFormatError


class TestScopeSetCreation(unittest.TestCase):
    """Test scope set creation and parsing."""

    def test_create_from_comma_string(self):
        scopes = ScopeSet("read_products, write_orders")
        self.assertIn("read_products", scopes)
        self.assertIn("write_orders", scopes)

    def test_create_from_list(self):
        scopes = ScopeSet(["read_products", "write_orders"])
        self.assertIn("read_products", scopes)
        self.assertIn("write_orders", scopes)

    def test_strips_whitespace(self):
        scopes = ScopeSet("  read_products  ,  write_orders  ")
        self.assertEqual(2, len(scopes))

    def test_ignores_empty_strings(self):
        scopes = ScopeSet("read_products,,write_orders")
        self.assertEqual(2, len(scopes))


class TestScopeValidation(unittest.TestCase):
    """Test scope format validation."""

    def test_valid_read_scope(self):
        scopes = ScopeSet("read_products")
        self.assertIn("read_products", scopes)

    def test_valid_write_scope(self):
        scopes = ScopeSet("write_orders")
        self.assertIn("write_orders", scopes)

    def test_invalid_scope_raises_error(self):
        with self.assertRaises(ScopeFormatError):
            ScopeSet("invalid")

    def test_missing_resource_raises_error(self):
        with self.assertRaises(ScopeFormatError):
            ScopeSet("read_")

    def test_invalid_action_raises_error(self):
        with self.assertRaises(ScopeFormatError):
            ScopeSet("delete_products")


class TestUnauthenticatedScopes(unittest.TestCase):
    """Test unauthenticated scope handling."""

    def test_unauthenticated_read_scope(self):
        scopes = ScopeSet("unauthenticated_read_products")
        self.assertIn("unauthenticated_read_products", scopes)

    def test_unauthenticated_write_scope(self):
        scopes = ScopeSet("unauthenticated_write_orders")
        self.assertIn("unauthenticated_write_orders", scopes)

    def test_unauthenticated_write_implies_read(self):
        scopes = ScopeSet("unauthenticated_write_products")
        self.assertIn("unauthenticated_read_products", scopes)


class TestScopeImplication(unittest.TestCase):
    """Test write scope implies read scope."""

    def test_write_implies_read(self):
        scopes = ScopeSet("write_products")
        self.assertIn("read_products", scopes)
        self.assertIn("write_products", scopes)

    def test_read_only_does_not_imply_write(self):
        scopes = ScopeSet("read_products")
        self.assertIn("read_products", scopes)
        self.assertNotIn("write_products", scopes)


class TestScopeCompression(unittest.TestCase):
    """Test scope compression behavior."""

    def test_write_and_read_compressed_to_write(self):
        scopes = ScopeSet("write_products, read_products")
        compressed = list(scopes)
        self.assertEqual(1, len(compressed))
        self.assertIn("write_products", compressed)

    def test_multiple_write_scopes_compressed(self):
        scopes = ScopeSet(
            "write_products, read_products, write_orders, read_orders"
        )
        compressed = list(scopes)
        self.assertEqual(2, len(compressed))

    def test_different_resources_not_compressed(self):
        scopes = ScopeSet("write_products, read_orders")
        self.assertEqual(2, len(scopes))


class TestScopeCovers(unittest.TestCase):
    """Test scope coverage checking."""

    def test_same_scopes_cover(self):
        a = ScopeSet("read_products, write_orders")
        b = ScopeSet("read_products, write_orders")
        self.assertTrue(a.covers(b))
        self.assertTrue(b.covers(a))

    def test_superset_covers_subset(self):
        superset = ScopeSet("write_products, write_orders")
        subset = ScopeSet("read_products")
        self.assertTrue(superset.covers(subset))

    def test_subset_does_not_cover_superset(self):
        superset = ScopeSet("write_products, write_orders")
        subset = ScopeSet("read_products")
        self.assertFalse(subset.covers(superset))

    def test_write_covers_read(self):
        write_scopes = ScopeSet("write_products")
        read_scopes = ScopeSet("read_products")
        self.assertTrue(write_scopes.covers(read_scopes))

    def test_read_does_not_cover_write(self):
        write_scopes = ScopeSet("write_products")
        read_scopes = ScopeSet("read_products")
        self.assertFalse(read_scopes.covers(write_scopes))


class TestScopeSetIteration(unittest.TestCase):
    """Test scope set iteration."""

    def test_iterate_yields_compressed_scopes(self):
        scopes = ScopeSet("write_products, read_products, read_orders")
        result = list(scopes)
        self.assertIn("write_products", result)
        self.assertIn("read_orders", result)
        self.assertNotIn("read_products", result)

    def test_len_returns_compressed_count(self):
        scopes = ScopeSet("write_products, read_products")
        self.assertEqual(1, len(scopes))


class TestScopeSetEquality(unittest.TestCase):
    """Test scope set equality."""

    def test_equal_scopes(self):
        a = ScopeSet("read_products, write_orders")
        b = ScopeSet("write_orders, read_products")
        self.assertEqual(a, b)

    def test_unequal_scopes(self):
        a = ScopeSet("read_products")
        b = ScopeSet("write_products")
        self.assertNotEqual(a, b)

    def test_not_equal_to_non_scopeset(self):
        scopes = ScopeSet("read_products")
        self.assertNotEqual(scopes, "read_products")

    def test_write_with_implied_read_equals_write_only(self):
        a = ScopeSet("write_products, read_products")
        b = ScopeSet("write_products")
        self.assertEqual(a, b)


class TestScopeSetString(unittest.TestCase):
    """Test scope set string representation."""

    def test_str_returns_comma_joined(self):
        scopes = ScopeSet("read_products, write_orders")
        result = str(scopes)
        self.assertIn("read_products", result)
        self.assertIn("write_orders", result)

    def test_repr_contains_scopes(self):
        scopes = ScopeSet("read_products")
        result = repr(scopes)
        self.assertIn("read_products", result)


if __name__ == "__main__":
    unittest.main()
