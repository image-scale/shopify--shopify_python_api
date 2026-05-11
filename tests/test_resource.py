"""Tests for the resource base class."""

import json
import threading
import unittest
from unittest.mock import patch, MagicMock

from shopify_api import (
    ShopSession,
    ResourceBase,
    ResourceError,
    ResourceNotFound,
)


class TestResource(ResourceBase):
    """Test resource class."""
    _resource_name = "product"
    _resource_name_plural = "products"


class NestedResource(ResourceBase):
    """Test nested resource class."""
    _resource_name = "fulfillment"
    _resource_name_plural = "fulfillments"
    _prefix_path = "/orders/$order_id"


class TestSessionManagement(unittest.TestCase):
    """Test session activation and clearing."""

    def setUp(self):
        ResourceBase.clear_session()
        ShopSession._domain_suffix = "myshopify.com"
        ShopSession._port = None

    def test_activate_session_sets_site(self):
        session = ShopSession("testshop", "2024-07", "token123")
        ResourceBase.activate_session(session)

        self.assertEqual(
            "https://testshop.myshopify.com/admin/api/2024-07",
            ResourceBase.get_site()
        )

    def test_activate_session_sets_headers(self):
        session = ShopSession("testshop", "2024-07", "token123")
        ResourceBase.activate_session(session)

        headers = ResourceBase.get_headers()
        self.assertEqual("token123", headers.get("X-Shopify-Access-Token"))

    def test_clear_session_removes_state(self):
        session = ShopSession("testshop", "2024-07", "token123")
        ResourceBase.activate_session(session)
        ResourceBase.clear_session()

        self.assertIsNone(ResourceBase.get_site())
        self.assertEqual({}, ResourceBase.get_headers())


class TestResourceAttributes(unittest.TestCase):
    """Test resource attribute handling."""

    def test_create_with_attributes(self):
        resource = TestResource({"title": "Test Product", "id": 123})
        self.assertEqual("Test Product", resource.title)
        self.assertEqual(123, resource.id)

    def test_set_attribute(self):
        resource = TestResource()
        resource.title = "New Title"
        self.assertEqual("New Title", resource.title)

    def test_is_new_without_id(self):
        resource = TestResource({"title": "Test"})
        self.assertTrue(resource.is_new())

    def test_is_not_new_with_id(self):
        resource = TestResource({"title": "Test", "id": 123})
        self.assertFalse(resource.is_new())

    def test_attributes_dict(self):
        resource = TestResource({"title": "Test", "price": 19.99})
        attrs = resource.attributes
        self.assertEqual("Test", attrs["title"])
        self.assertEqual(19.99, attrs["price"])


class TestResourcePaths(unittest.TestCase):
    """Test URL path generation."""

    def setUp(self):
        ResourceBase.clear_session()
        session = ShopSession("testshop", "2024-07", "token123")
        ResourceBase.activate_session(session)

    def test_collection_path(self):
        path = TestResource._collection_path()
        self.assertEqual(
            "https://testshop.myshopify.com/admin/api/2024-07/products.json",
            path
        )

    def test_collection_path_with_params(self):
        path = TestResource._collection_path(query_params={"limit": 10})
        self.assertIn("limit=10", path)

    def test_element_path(self):
        path = TestResource._element_path(123)
        self.assertEqual(
            "https://testshop.myshopify.com/admin/api/2024-07/products/123.json",
            path
        )

    def test_nested_resource_path(self):
        path = NestedResource._collection_path({"order_id": 456})
        self.assertEqual(
            "https://testshop.myshopify.com/admin/api/2024-07/orders/456/fulfillments.json",
            path
        )


class TestResourceFind(unittest.TestCase):
    """Test resource finding operations."""

    def setUp(self):
        ResourceBase.clear_session()
        session = ShopSession("testshop", "2024-07", "token123")
        ResourceBase.activate_session(session)

    @patch("shopify_api.resource.urlopen")
    def test_find_by_id(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "product": {"id": 123, "title": "Test Product"}
        }).encode("utf-8")
        mock_urlopen.return_value = mock_response

        resource = TestResource.find(123)

        self.assertEqual(123, resource.id)
        self.assertEqual("Test Product", resource.title)

    @patch("shopify_api.resource.urlopen")
    def test_find_collection(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "products": [
                {"id": 1, "title": "Product 1"},
                {"id": 2, "title": "Product 2"},
            ]
        }).encode("utf-8")
        mock_urlopen.return_value = mock_response

        resources = TestResource.find()

        self.assertEqual(2, len(resources))
        self.assertEqual(1, resources[0].id)
        self.assertEqual(2, resources[1].id)

    @patch("shopify_api.resource.urlopen")
    def test_find_with_query_params(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "products": [{"id": 1}]
        }).encode("utf-8")
        mock_urlopen.return_value = mock_response

        TestResource.find(limit=10, status="active")

        call_args = mock_urlopen.call_args
        url = call_args[0][0].full_url
        self.assertIn("limit=10", url)
        self.assertIn("status=active", url)

    @patch("shopify_api.resource.urlopen")
    def test_find_nested_resource(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "fulfillments": [{"id": 789}]
        }).encode("utf-8")
        mock_urlopen.return_value = mock_response

        resources = NestedResource.find(order_id=456)

        call_args = mock_urlopen.call_args
        url = call_args[0][0].full_url
        self.assertIn("/orders/456/fulfillments", url)


class TestResourceSave(unittest.TestCase):
    """Test resource save operations."""

    def setUp(self):
        ResourceBase.clear_session()
        session = ShopSession("testshop", "2024-07", "token123")
        ResourceBase.activate_session(session)

    @patch("shopify_api.resource.urlopen")
    def test_save_creates_new_resource(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "product": {"id": 123, "title": "New Product"}
        }).encode("utf-8")
        mock_urlopen.return_value = mock_response

        resource = TestResource({"title": "New Product"})
        result = resource.save()

        self.assertTrue(result)
        self.assertEqual(123, resource.id)

        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        self.assertEqual("POST", request.method)

    @patch("shopify_api.resource.urlopen")
    def test_save_updates_existing_resource(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "product": {"id": 123, "title": "Updated"}
        }).encode("utf-8")
        mock_urlopen.return_value = mock_response

        resource = TestResource({"id": 123, "title": "Updated"})
        result = resource.save()

        self.assertTrue(result)

        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        self.assertEqual("PUT", request.method)


class TestResourceDestroy(unittest.TestCase):
    """Test resource delete operations."""

    def setUp(self):
        ResourceBase.clear_session()
        session = ShopSession("testshop", "2024-07", "token123")
        ResourceBase.activate_session(session)

    @patch("shopify_api.resource.urlopen")
    def test_destroy_deletes_resource(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = b""
        mock_urlopen.return_value = mock_response

        resource = TestResource({"id": 123})
        result = resource.destroy()

        self.assertTrue(result)

        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        self.assertEqual("DELETE", request.method)

    def test_destroy_unsaved_raises_error(self):
        resource = TestResource({"title": "New"})

        with self.assertRaises(ResourceError):
            resource.destroy()


class TestResourceCount(unittest.TestCase):
    """Test resource counting."""

    def setUp(self):
        ResourceBase.clear_session()
        session = ShopSession("testshop", "2024-07", "token123")
        ResourceBase.activate_session(session)

    @patch("shopify_api.resource.urlopen")
    def test_count_returns_integer(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "count": 42
        }).encode("utf-8")
        mock_urlopen.return_value = mock_response

        count = TestResource.count()

        self.assertEqual(42, count)


class TestResourceExists(unittest.TestCase):
    """Test resource existence checking."""

    def setUp(self):
        ResourceBase.clear_session()
        session = ShopSession("testshop", "2024-07", "token123")
        ResourceBase.activate_session(session)

    @patch("shopify_api.resource.urlopen")
    def test_exists_returns_true(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "product": {"id": 123}
        }).encode("utf-8")
        mock_urlopen.return_value = mock_response

        self.assertTrue(TestResource.exists(123))

    @patch("shopify_api.resource.urlopen")
    def test_exists_returns_false_when_not_found(self, mock_urlopen):
        from urllib.error import HTTPError
        mock_urlopen.side_effect = HTTPError(
            url="", code=404, msg="Not Found", hdrs={}, fp=None
        )

        self.assertFalse(TestResource.exists(999))


class TestThreadSafety(unittest.TestCase):
    """Test thread-local session state."""

    def setUp(self):
        ResourceBase.clear_session()

    def test_sessions_are_thread_local(self):
        results = {}

        def thread_func(thread_id, shop_name):
            session = ShopSession(shop_name, "2024-07", f"token_{thread_id}")
            ResourceBase.activate_session(session)
            import time
            time.sleep(0.01)
            results[thread_id] = ResourceBase.get_site()

        threads = [
            threading.Thread(target=thread_func, args=(1, "shop1")),
            threading.Thread(target=thread_func, args=(2, "shop2")),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertIn("shop1", results[1])
        self.assertIn("shop2", results[2])


class TestNoSession(unittest.TestCase):
    """Test behavior without active session."""

    def setUp(self):
        ResourceBase.clear_session()

    def test_find_without_session_raises_error(self):
        with self.assertRaises(ResourceError):
            TestResource.find(123)


if __name__ == "__main__":
    unittest.main()
