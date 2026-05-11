"""Tests for pagination support."""

import unittest
from unittest.mock import MagicMock, patch

from shopify_api import PaginatedCollection, PageIterator, ResourceBase


class MockResource(ResourceBase):
    """Mock resource for testing."""
    _resource_name = "item"
    _resource_name_plural = "items"


class TestPaginatedCollection(unittest.TestCase):
    """Test paginated collection."""

    def test_collection_is_a_list(self):
        items = [{"id": 1}, {"id": 2}]
        collection = PaginatedCollection(items)

        self.assertIsInstance(collection, list)
        self.assertEqual(2, len(collection))
        self.assertEqual({"id": 1}, collection[0])

    def test_has_next_page_with_url(self):
        collection = PaginatedCollection(
            [],
            next_url="https://shop.com/next"
        )
        self.assertTrue(collection.has_next_page())

    def test_has_next_page_without_url(self):
        collection = PaginatedCollection([])
        self.assertFalse(collection.has_next_page())

    def test_has_previous_page_with_url(self):
        collection = PaginatedCollection(
            [],
            previous_url="https://shop.com/prev"
        )
        self.assertTrue(collection.has_previous_page())

    def test_has_previous_page_without_url(self):
        collection = PaginatedCollection([])
        self.assertFalse(collection.has_previous_page())

    def test_next_page_url_property(self):
        collection = PaginatedCollection(
            [],
            next_url="https://shop.com/next"
        )
        self.assertEqual("https://shop.com/next", collection.next_page_url)

    def test_previous_page_url_property(self):
        collection = PaginatedCollection(
            [],
            previous_url="https://shop.com/prev"
        )
        self.assertEqual("https://shop.com/prev", collection.previous_page_url)

    def test_next_page_raises_when_no_next(self):
        collection = PaginatedCollection([])

        with self.assertRaises(IndexError) as context:
            collection.next_page()

        self.assertIn("No next page", str(context.exception))

    def test_previous_page_raises_when_no_previous(self):
        collection = PaginatedCollection([])

        with self.assertRaises(IndexError) as context:
            collection.previous_page()

        self.assertIn("No previous page", str(context.exception))

    def test_next_page_caches_result(self):
        collection = PaginatedCollection(
            [{"id": 1}],
            resource_class=MockResource,
            next_url="https://shop.com/next"
        )

        with patch.object(MockResource, "find") as mock_find:
            mock_find.return_value = PaginatedCollection([{"id": 2}], MockResource)

            page2_first = collection.next_page()
            page2_second = collection.next_page()

            mock_find.assert_called_once()
            self.assertIs(page2_first, page2_second)

    def test_next_page_no_cache_skips_cache(self):
        collection = PaginatedCollection(
            [{"id": 1}],
            resource_class=MockResource,
            next_url="https://shop.com/next"
        )

        with patch.object(MockResource, "find") as mock_find:
            mock_find.return_value = PaginatedCollection([{"id": 2}], MockResource)

            collection.next_page(no_cache=True)
            collection.next_page(no_cache=True)

            self.assertEqual(2, mock_find.call_count)


class TestLinkHeaderParsing(unittest.TestCase):
    """Test Link header parsing."""

    def test_parse_next_link(self):
        header = '<https://shop.com/products?page_info=next>; rel="next"'
        result = PaginatedCollection._parse_link_header(header)

        self.assertEqual("https://shop.com/products?page_info=next", result["next"])

    def test_parse_previous_link(self):
        header = '<https://shop.com/products?page_info=prev>; rel="previous"'
        result = PaginatedCollection._parse_link_header(header)

        self.assertEqual("https://shop.com/products?page_info=prev", result["previous"])

    def test_parse_both_links(self):
        header = '<https://shop.com/prev>; rel="previous", <https://shop.com/next>; rel="next"'
        result = PaginatedCollection._parse_link_header(header)

        self.assertEqual("https://shop.com/prev", result["previous"])
        self.assertEqual("https://shop.com/next", result["next"])

    def test_from_response_creates_collection(self):
        items = [{"id": 1}, {"id": 2}]
        headers = {
            "Link": '<https://shop.com/next>; rel="next"'
        }

        collection = PaginatedCollection.from_response(
            items, MockResource, headers
        )

        self.assertEqual(2, len(collection))
        self.assertTrue(collection.has_next_page())
        self.assertFalse(collection.has_previous_page())

    def test_from_response_lowercase_link_header(self):
        items = []
        headers = {
            "link": '<https://shop.com/next>; rel="next"'
        }

        collection = PaginatedCollection.from_response(
            items, MockResource, headers
        )

        self.assertTrue(collection.has_next_page())


class TestPageIterator(unittest.TestCase):
    """Test page iterator."""

    def test_iterator_requires_paginated_collection(self):
        with self.assertRaises(TypeError):
            PageIterator([1, 2, 3])

    def test_iterator_yields_first_page(self):
        collection = PaginatedCollection(
            [{"id": 1}],
            resource_class=MockResource
        )

        iterator = PageIterator(collection)
        pages = list(iterator)

        self.assertEqual(1, len(pages))
        self.assertIs(collection, pages[0])

    def test_iterator_fetches_all_pages(self):
        page3 = PaginatedCollection([{"id": 3}], MockResource)
        page2 = PaginatedCollection(
            [{"id": 2}],
            MockResource,
            next_url="https://shop.com/page3"
        )
        page1 = PaginatedCollection(
            [{"id": 1}],
            MockResource,
            next_url="https://shop.com/page2"
        )

        with patch.object(MockResource, "find") as mock_find:
            mock_find.side_effect = [page2, page3]

            iterator = PageIterator(page1)
            pages = list(iterator)

            self.assertEqual(3, len(pages))
            self.assertEqual([{"id": 1}], list(pages[0]))
            self.assertEqual([{"id": 2}], list(pages[1]))
            self.assertEqual([{"id": 3}], list(pages[2]))


if __name__ == "__main__":
    unittest.main()
