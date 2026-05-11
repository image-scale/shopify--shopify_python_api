"""Tests for Shop, Metafield, and Event resources."""

import json
import unittest
from unittest.mock import patch, MagicMock

from shopify_api import (
    ShopSession,
    ResourceBase,
    Shop,
    Metafield,
    Event,
)


class TestShopResource(unittest.TestCase):
    """Test Shop resource."""

    def setUp(self):
        ResourceBase.clear_session()
        session = ShopSession("testshop", "2024-07", "token123")
        ResourceBase.activate_session(session)

    @patch("shopify_api.resource.urlopen")
    def test_shop_current_retrieves_shop(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "shop": {
                "id": 12345,
                "name": "Test Shop",
                "email": "test@example.com",
                "domain": "test-shop.com",
                "myshopify_domain": "testshop.myshopify.com",
                "shop_owner": "Test Owner",
                "plan_name": "basic",
                "currency": "USD",
                "timezone": "America/New_York",
                "country": "US",
                "created_at": "2020-01-01T00:00:00-05:00"
            }
        }).encode("utf-8")
        mock_urlopen.return_value = mock_response

        shop = Shop.current()

        self.assertEqual(12345, shop.id)
        self.assertEqual("Test Shop", shop.name)
        self.assertEqual("test@example.com", shop.email)
        self.assertEqual("test-shop.com", shop.domain)
        self.assertEqual("testshop.myshopify.com", shop.myshopify_domain)
        self.assertEqual("Test Owner", shop.shop_owner)
        self.assertEqual("basic", shop.plan_name)
        self.assertEqual("USD", shop.currency)
        self.assertEqual("America/New_York", shop.timezone)
        self.assertEqual("US", shop.country)

    @patch("shopify_api.resource.urlopen")
    def test_shop_metafields(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "metafields": [
                {"id": 1, "namespace": "inventory", "key": "warehouse", "value": "NYC"},
                {"id": 2, "namespace": "contact", "key": "phone", "value": "555-1234"},
            ]
        }).encode("utf-8")
        mock_urlopen.return_value = mock_response

        shop = Shop({"id": 12345})
        shop._persisted = True
        metafields = shop.metafields()

        self.assertEqual(2, len(metafields))
        self.assertIsInstance(metafields[0], Metafield)
        self.assertEqual("inventory", metafields[0].namespace)
        self.assertEqual("warehouse", metafields[0].key)

    @patch("shopify_api.resource.urlopen")
    def test_shop_add_metafield(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "metafield": {
                "id": 123,
                "namespace": "settings",
                "key": "color",
                "value": "blue",
                "value_type": "string"
            }
        }).encode("utf-8")
        mock_urlopen.return_value = mock_response

        shop = Shop({"id": 12345})
        shop._persisted = True

        metafield = Metafield({
            "namespace": "settings",
            "key": "color",
            "value": "blue",
            "value_type": "string"
        })
        result = shop.add_metafield(metafield)

        self.assertEqual(123, result.id)
        self.assertEqual("settings", result.namespace)
        self.assertEqual("color", result.key)
        self.assertEqual("blue", result.value)

    def test_shop_add_metafield_requires_saved_shop(self):
        shop = Shop({"name": "New Shop"})

        metafield = Metafield({"namespace": "test", "key": "foo"})

        with self.assertRaises(ValueError):
            shop.add_metafield(metafield)

    @patch("shopify_api.resource.urlopen")
    def test_shop_events(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "events": [
                {
                    "id": 1,
                    "subject_type": "Order",
                    "subject_id": 555,
                    "verb": "placed",
                    "created_at": "2024-01-01T12:00:00-05:00"
                },
                {
                    "id": 2,
                    "subject_type": "Product",
                    "subject_id": 666,
                    "verb": "create",
                    "created_at": "2024-01-02T12:00:00-05:00"
                }
            ]
        }).encode("utf-8")
        mock_urlopen.return_value = mock_response

        shop = Shop({"id": 12345})
        shop._persisted = True
        events = shop.events()

        self.assertEqual(2, len(events))
        self.assertIsInstance(events[0], Event)
        self.assertEqual("Order", events[0].subject_type)
        self.assertEqual("placed", events[0].verb)


class TestMetafieldResource(unittest.TestCase):
    """Test Metafield resource."""

    def setUp(self):
        ResourceBase.clear_session()
        session = ShopSession("testshop", "2024-07", "token123")
        ResourceBase.activate_session(session)

    def test_metafield_attributes(self):
        metafield = Metafield({
            "id": 100,
            "namespace": "inventory",
            "key": "warehouse",
            "value": "NYC",
            "value_type": "string"
        })

        self.assertEqual("inventory", metafield.namespace)
        self.assertEqual("warehouse", metafield.key)
        self.assertEqual("NYC", metafield.value)
        self.assertEqual("string", metafield.value_type)

    @patch("shopify_api.resource.urlopen")
    def test_metafield_find(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "metafield": {
                "id": 100,
                "namespace": "inventory",
                "key": "warehouse",
                "value": "NYC"
            }
        }).encode("utf-8")
        mock_urlopen.return_value = mock_response

        metafield = Metafield.find(100)

        self.assertEqual(100, metafield.id)
        self.assertEqual("inventory", metafield.namespace)

    @patch("shopify_api.resource.urlopen")
    def test_metafield_save(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "metafield": {
                "id": 200,
                "namespace": "settings",
                "key": "theme",
                "value": "dark"
            }
        }).encode("utf-8")
        mock_urlopen.return_value = mock_response

        metafield = Metafield({
            "namespace": "settings",
            "key": "theme",
            "value": "dark"
        })
        result = metafield.save()

        self.assertTrue(result)
        self.assertEqual(200, metafield.id)

    @patch("shopify_api.resource.urlopen")
    def test_metafield_destroy(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = b""
        mock_urlopen.return_value = mock_response

        metafield = Metafield({"id": 100})
        result = metafield.destroy()

        self.assertTrue(result)

        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        self.assertEqual("DELETE", request.method)


class TestEventResource(unittest.TestCase):
    """Test Event resource."""

    def setUp(self):
        ResourceBase.clear_session()
        session = ShopSession("testshop", "2024-07", "token123")
        ResourceBase.activate_session(session)

    def test_event_attributes(self):
        event = Event({
            "id": 1,
            "subject_type": "Order",
            "subject_id": 555,
            "verb": "placed",
            "message": "Order was placed",
            "created_at": "2024-01-01T12:00:00-05:00",
            "arguments": ["arg1", "arg2"]
        })

        self.assertEqual("Order", event.subject_type)
        self.assertEqual(555, event.subject_id)
        self.assertEqual("placed", event.verb)
        self.assertEqual("Order was placed", event.message)
        self.assertEqual("2024-01-01T12:00:00-05:00", event.created_at)
        self.assertEqual(["arg1", "arg2"], event.arguments)

    @patch("shopify_api.resource.urlopen")
    def test_event_find_collection(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "events": [
                {"id": 1, "subject_type": "Order", "verb": "placed"},
                {"id": 2, "subject_type": "Product", "verb": "create"},
                {"id": 3, "subject_type": "Customer", "verb": "create"}
            ]
        }).encode("utf-8")
        mock_urlopen.return_value = mock_response

        events = Event.find()

        self.assertEqual(3, len(events))
        self.assertIsInstance(events[0], Event)
        self.assertEqual("Order", events[0].subject_type)

    @patch("shopify_api.resource.urlopen")
    def test_event_find_by_id(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "event": {
                "id": 1,
                "subject_type": "Order",
                "subject_id": 555,
                "verb": "placed"
            }
        }).encode("utf-8")
        mock_urlopen.return_value = mock_response

        event = Event.find(1)

        self.assertEqual(1, event.id)
        self.assertEqual("Order", event.subject_type)
        self.assertEqual(555, event.subject_id)


if __name__ == "__main__":
    unittest.main()
