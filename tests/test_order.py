"""Tests for Customer, Order, Transaction, and Fulfillment resources."""

import json
import unittest
from unittest.mock import patch, MagicMock

from shopify_api import (
    ShopSession,
    ResourceBase,
    Customer,
    Order,
    Transaction,
    Fulfillment,
    Metafield,
)


class TestCustomerResource(unittest.TestCase):
    """Test Customer resource."""

    def setUp(self):
        ResourceBase.clear_session()
        session = ShopSession("testshop", "2024-07", "token123")
        ResourceBase.activate_session(session)

    @patch("shopify_api.resource.urlopen")
    def test_customer_find_by_id(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "customer": {
                "id": 123,
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
                "phone": "+1234567890",
                "orders_count": 5,
                "total_spent": "250.00",
                "verified_email": True,
                "accepts_marketing": False,
                "state": "enabled"
            }
        }).encode("utf-8")
        mock_urlopen.return_value = mock_response

        customer = Customer.find(123)

        self.assertEqual(123, customer.id)
        self.assertEqual("John", customer.first_name)
        self.assertEqual("Doe", customer.last_name)
        self.assertEqual("john@example.com", customer.email)
        self.assertEqual(5, customer.orders_count)
        self.assertEqual("250.00", customer.total_spent)
        self.assertTrue(customer.verified_email)
        self.assertFalse(customer.accepts_marketing)

    @patch("shopify_api.resource.urlopen")
    def test_customer_search(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "customers": [
                {"id": 1, "email": "john@example.com"},
                {"id": 2, "email": "jane@example.com"}
            ]
        }).encode("utf-8")
        mock_urlopen.return_value = mock_response

        customers = Customer.search(query="email:example.com")

        self.assertEqual(2, len(customers))
        self.assertEqual("john@example.com", customers[0].email)

    @patch("shopify_api.resource.urlopen")
    def test_customer_send_invite(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "customer_invite": {
                "to": "john@example.com",
                "subject": "Welcome!",
                "custom_message": "Please create your account."
            }
        }).encode("utf-8")
        mock_urlopen.return_value = mock_response

        customer = Customer({"id": 123, "email": "john@example.com"})
        customer._persisted = True
        result = customer.send_invite()

        self.assertEqual("john@example.com", result.get("to"))


class TestOrderResource(unittest.TestCase):
    """Test Order resource."""

    def setUp(self):
        ResourceBase.clear_session()
        session = ShopSession("testshop", "2024-07", "token123")
        ResourceBase.activate_session(session)

    @patch("shopify_api.resource.urlopen")
    def test_order_find_by_id(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "order": {
                "id": 456,
                "order_number": 1001,
                "name": "#1001",
                "email": "customer@example.com",
                "total_price": "99.99",
                "subtotal_price": "89.99",
                "total_tax": "10.00",
                "currency": "USD",
                "financial_status": "paid",
                "fulfillment_status": None,
                "line_items": [
                    {"id": 1, "title": "Product A", "quantity": 2}
                ]
            }
        }).encode("utf-8")
        mock_urlopen.return_value = mock_response

        order = Order.find(456)

        self.assertEqual(456, order.id)
        self.assertEqual(1001, order.order_number)
        self.assertEqual("#1001", order.name)
        self.assertEqual("99.99", order.total_price)
        self.assertEqual("paid", order.financial_status)
        self.assertEqual(1, len(order.line_items))

    @patch("shopify_api.resource.urlopen")
    def test_order_close(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "order": {"id": 456, "closed_at": "2024-01-15T12:00:00-05:00"}
        }).encode("utf-8")
        mock_urlopen.return_value = mock_response

        order = Order({"id": 456}, {})
        order._persisted = True
        order.close()

        self.assertIsNotNone(order.closed_at)

    @patch("shopify_api.resource.urlopen")
    def test_order_open(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "order": {"id": 456, "closed_at": None}
        }).encode("utf-8")
        mock_urlopen.return_value = mock_response

        order = Order({"id": 456, "closed_at": "2024-01-15"}, {})
        order._persisted = True
        order.open()

        self.assertIsNone(order.closed_at)

    @patch("shopify_api.resource.urlopen")
    def test_order_cancel(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "order": {"id": 456, "cancelled_at": "2024-01-15T12:00:00-05:00"}
        }).encode("utf-8")
        mock_urlopen.return_value = mock_response

        order = Order({"id": 456}, {})
        order._persisted = True
        order.cancel(reason="customer")

        self.assertIsNotNone(order.cancelled_at)

    @patch("shopify_api.resource.urlopen")
    def test_order_transactions(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "transactions": [
                {"id": 1, "kind": "sale", "status": "success", "amount": "99.99"}
            ]
        }).encode("utf-8")
        mock_urlopen.return_value = mock_response

        order = Order({"id": 456})
        order._persisted = True
        transactions = order.transactions()

        self.assertEqual(1, len(transactions))
        self.assertIsInstance(transactions[0], Transaction)
        self.assertEqual("sale", transactions[0].kind)

    @patch("shopify_api.resource.urlopen")
    def test_order_capture(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "transaction": {
                "id": 789,
                "kind": "capture",
                "amount": "99.99",
                "status": "success"
            }
        }).encode("utf-8")
        mock_urlopen.return_value = mock_response

        order = Order({"id": 456, "total_price": "99.99"})
        order._persisted = True
        transaction = order.capture()

        self.assertEqual(789, transaction.id)
        self.assertEqual("capture", transaction.kind)

    @patch("shopify_api.resource.urlopen")
    def test_order_fulfillments(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "fulfillments": [
                {"id": 1, "status": "success", "tracking_number": "1Z999999"}
            ]
        }).encode("utf-8")
        mock_urlopen.return_value = mock_response

        order = Order({"id": 456})
        order._persisted = True
        fulfillments = order.fulfillments()

        self.assertEqual(1, len(fulfillments))
        self.assertIsInstance(fulfillments[0], Fulfillment)


class TestTransactionResource(unittest.TestCase):
    """Test Transaction resource."""

    def setUp(self):
        ResourceBase.clear_session()
        session = ShopSession("testshop", "2024-07", "token123")
        ResourceBase.activate_session(session)

    def test_transaction_attributes(self):
        transaction = Transaction({
            "id": 123,
            "kind": "sale",
            "status": "success",
            "amount": "99.99",
            "currency": "USD",
            "gateway": "shopify_payments",
            "authorization": "ABC123",
            "created_at": "2024-01-15T12:00:00-05:00"
        })

        self.assertEqual("sale", transaction.kind)
        self.assertEqual("success", transaction.status)
        self.assertEqual("99.99", transaction.amount)
        self.assertEqual("USD", transaction.currency)
        self.assertEqual("shopify_payments", transaction.gateway)

    @patch("shopify_api.resource.urlopen")
    def test_transaction_find(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "transaction": {
                "id": 123,
                "kind": "refund",
                "amount": "50.00"
            }
        }).encode("utf-8")
        mock_urlopen.return_value = mock_response

        transaction = Transaction.find(123, order_id=456)

        self.assertEqual(123, transaction.id)
        self.assertEqual("refund", transaction.kind)


class TestFulfillmentResource(unittest.TestCase):
    """Test Fulfillment resource."""

    def setUp(self):
        ResourceBase.clear_session()
        session = ShopSession("testshop", "2024-07", "token123")
        ResourceBase.activate_session(session)

    def test_fulfillment_attributes(self):
        fulfillment = Fulfillment({
            "id": 123,
            "status": "success",
            "tracking_number": "1Z999999",
            "tracking_url": "https://ups.com/track/1Z999999",
            "tracking_company": "UPS",
            "shipment_status": "delivered"
        })

        self.assertEqual("success", fulfillment.status)
        self.assertEqual("1Z999999", fulfillment.tracking_number)
        self.assertEqual("https://ups.com/track/1Z999999", fulfillment.tracking_url)
        self.assertEqual("UPS", fulfillment.tracking_company)
        self.assertEqual("delivered", fulfillment.shipment_status)

    @patch("shopify_api.resource.urlopen")
    def test_fulfillment_cancel(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "fulfillment": {"id": 123, "status": "cancelled"}
        }).encode("utf-8")
        mock_urlopen.return_value = mock_response

        fulfillment = Fulfillment({"id": 123}, {"order_id": 456})
        fulfillment._persisted = True
        fulfillment.cancel()

        self.assertEqual("cancelled", fulfillment.status)

    @patch("shopify_api.resource.urlopen")
    def test_fulfillment_complete(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "fulfillment": {"id": 123, "status": "success"}
        }).encode("utf-8")
        mock_urlopen.return_value = mock_response

        fulfillment = Fulfillment({"id": 123, "status": "pending"}, {"order_id": 456})
        fulfillment._persisted = True
        fulfillment.complete()

        self.assertEqual("success", fulfillment.status)


if __name__ == "__main__":
    unittest.main()
