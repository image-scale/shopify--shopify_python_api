"""Tests for Product, Variant, and Image resources."""

import json
import unittest
from unittest.mock import patch, MagicMock

from shopify_api import (
    ShopSession,
    ResourceBase,
    Product,
    Variant,
    Image,
    Metafield,
)


class TestProductResource(unittest.TestCase):
    """Test Product resource."""

    def setUp(self):
        ResourceBase.clear_session()
        session = ShopSession("testshop", "2024-07", "token123")
        ResourceBase.activate_session(session)

    @patch("shopify_api.resource.urlopen")
    def test_product_find_by_id(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "product": {
                "id": 12345,
                "title": "Test Product",
                "body_html": "<p>Description</p>",
                "vendor": "Test Vendor",
                "product_type": "Widgets",
                "handle": "test-product",
                "tags": "tag1, tag2",
                "variants": [
                    {"id": 1, "price": "19.99", "sku": "SKU001"},
                    {"id": 2, "price": "29.99", "sku": "SKU002"}
                ],
                "images": [
                    {"id": 1, "src": "http://example.com/img1.jpg", "position": 1}
                ]
            }
        }).encode("utf-8")
        mock_urlopen.return_value = mock_response

        product = Product.find(12345)

        self.assertEqual(12345, product.id)
        self.assertEqual("Test Product", product.title)
        self.assertEqual("<p>Description</p>", product.body_html)
        self.assertEqual("Test Vendor", product.vendor)
        self.assertEqual("Widgets", product.product_type)
        self.assertEqual("test-product", product.handle)

    @patch("shopify_api.resource.urlopen")
    def test_product_find_collection(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "products": [
                {"id": 1, "title": "Product 1"},
                {"id": 2, "title": "Product 2"},
            ]
        }).encode("utf-8")
        mock_urlopen.return_value = mock_response

        products = Product.find()

        self.assertEqual(2, len(products))
        self.assertEqual("Product 1", products[0].title)

    def test_product_variants(self):
        product = Product({
            "id": 123,
            "title": "Test",
            "variants": [
                {"id": 1, "price": "19.99", "sku": "SKU001"},
                {"id": 2, "price": "29.99", "sku": "SKU002"}
            ]
        })

        variants = product.variants

        self.assertEqual(2, len(variants))
        self.assertIsInstance(variants[0], Variant)
        self.assertEqual("19.99", variants[0].price)
        self.assertEqual("SKU001", variants[0].sku)

    def test_product_images(self):
        product = Product({
            "id": 123,
            "title": "Test",
            "images": [
                {"id": 1, "src": "http://example.com/img1.jpg", "position": 1},
                {"id": 2, "src": "http://example.com/img2.jpg", "position": 2}
            ]
        })

        images = product.images

        self.assertEqual(2, len(images))
        self.assertIsInstance(images[0], Image)
        self.assertEqual("http://example.com/img1.jpg", images[0].src)
        self.assertEqual(1, images[0].position)

    def test_price_range_single_price(self):
        product = Product({
            "id": 123,
            "variants": [
                {"price": "19.99"},
                {"price": "19.99"}
            ]
        })

        self.assertEqual("19.99", product.price_range())

    def test_price_range_multiple_prices(self):
        product = Product({
            "id": 123,
            "variants": [
                {"price": "19.99"},
                {"price": "29.99"},
                {"price": "24.99"}
            ]
        })

        self.assertEqual("19.99 - 29.99", product.price_range())

    def test_price_range_no_variants(self):
        product = Product({"id": 123})
        self.assertEqual("0.00", product.price_range())

    @patch("shopify_api.resource.urlopen")
    def test_product_save(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "product": {
                "id": 12345,
                "title": "New Product"
            }
        }).encode("utf-8")
        mock_urlopen.return_value = mock_response

        product = Product({"title": "New Product"})
        result = product.save()

        self.assertTrue(result)
        self.assertEqual(12345, product.id)

    @patch("shopify_api.resource.urlopen")
    def test_product_metafields(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "metafields": [
                {"id": 1, "namespace": "inventory", "key": "warehouse", "value": "NYC"}
            ]
        }).encode("utf-8")
        mock_urlopen.return_value = mock_response

        product = Product({"id": 123})
        product._persisted = True
        metafields = product.metafields()

        self.assertEqual(1, len(metafields))
        self.assertIsInstance(metafields[0], Metafield)

    @patch("shopify_api.resource.urlopen")
    def test_product_add_metafield(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "metafield": {
                "id": 100,
                "namespace": "custom",
                "key": "color",
                "value": "red"
            }
        }).encode("utf-8")
        mock_urlopen.return_value = mock_response

        product = Product({"id": 123})
        product._persisted = True

        metafield = Metafield({
            "namespace": "custom",
            "key": "color",
            "value": "red"
        })
        result = product.add_metafield(metafield)

        self.assertEqual(100, result.id)

    def test_product_add_metafield_requires_saved(self):
        product = Product({"title": "New"})
        metafield = Metafield({"namespace": "test", "key": "foo"})

        with self.assertRaises(ValueError):
            product.add_metafield(metafield)

    @patch("shopify_api.resource.urlopen")
    def test_product_add_variant(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "variant": {
                "id": 456,
                "price": "25.00",
                "sku": "NEW-SKU"
            }
        }).encode("utf-8")
        mock_urlopen.return_value = mock_response

        product = Product({"id": 123})
        product._persisted = True

        variant = Variant({"price": "25.00", "sku": "NEW-SKU"})
        result = product.add_variant(variant)

        self.assertTrue(result)
        self.assertEqual(456, variant.id)


class TestVariantResource(unittest.TestCase):
    """Test Variant resource."""

    def setUp(self):
        ResourceBase.clear_session()
        session = ShopSession("testshop", "2024-07", "token123")
        ResourceBase.activate_session(session)

    def test_variant_attributes(self):
        variant = Variant({
            "id": 123,
            "price": "19.99",
            "sku": "SKU001",
            "inventory_quantity": 50,
            "title": "Small",
            "option1": "Small",
            "option2": "Blue",
            "weight": 200,
            "weight_unit": "g",
            "taxable": True,
            "barcode": "123456789"
        })

        self.assertEqual("19.99", variant.price)
        self.assertEqual("SKU001", variant.sku)
        self.assertEqual(50, variant.inventory_quantity)
        self.assertEqual("Small", variant.title)
        self.assertEqual("Small", variant.option1)
        self.assertEqual("Blue", variant.option2)
        self.assertEqual(200, variant.weight)
        self.assertEqual("g", variant.weight_unit)
        self.assertTrue(variant.taxable)
        self.assertEqual("123456789", variant.barcode)

    @patch("shopify_api.resource.urlopen")
    def test_variant_find_by_id(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "variant": {
                "id": 456,
                "price": "24.99",
                "sku": "SKU002"
            }
        }).encode("utf-8")
        mock_urlopen.return_value = mock_response

        variant = Variant.find(456, product_id=123)

        self.assertEqual(456, variant.id)
        self.assertEqual("24.99", variant.price)

    @patch("shopify_api.resource.urlopen")
    def test_variant_save(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "variant": {
                "id": 789,
                "price": "15.00"
            }
        }).encode("utf-8")
        mock_urlopen.return_value = mock_response

        variant = Variant({"price": "15.00"}, {"product_id": 123})
        result = variant.save()

        self.assertTrue(result)
        self.assertEqual(789, variant.id)

    @patch("shopify_api.resource.urlopen")
    def test_variant_update(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "variant": {
                "id": 456,
                "price": "30.00"
            }
        }).encode("utf-8")
        mock_urlopen.return_value = mock_response

        variant = Variant({"id": 456, "price": "30.00"}, {"product_id": 123})
        variant.price = "30.00"
        result = variant.save()

        self.assertTrue(result)

        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        self.assertEqual("PUT", request.method)


class TestImageResource(unittest.TestCase):
    """Test Image resource."""

    def setUp(self):
        ResourceBase.clear_session()
        session = ShopSession("testshop", "2024-07", "token123")
        ResourceBase.activate_session(session)

    def test_image_attributes(self):
        image = Image({
            "id": 100,
            "src": "http://example.com/image.jpg",
            "position": 2,
            "width": 800,
            "height": 600,
            "alt": "Product image",
            "variant_ids": [1, 2, 3]
        })

        self.assertEqual("http://example.com/image.jpg", image.src)
        self.assertEqual(2, image.position)
        self.assertEqual(800, image.width)
        self.assertEqual(600, image.height)
        self.assertEqual("Product image", image.alt)
        self.assertEqual([1, 2, 3], image.variant_ids)

    @patch("shopify_api.resource.urlopen")
    def test_image_find_by_id(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "image": {
                "id": 100,
                "src": "http://example.com/image.jpg",
                "position": 1
            }
        }).encode("utf-8")
        mock_urlopen.return_value = mock_response

        image = Image.find(100, product_id=123)

        self.assertEqual(100, image.id)
        self.assertEqual("http://example.com/image.jpg", image.src)

    @patch("shopify_api.resource.urlopen")
    def test_image_save(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "image": {
                "id": 200,
                "src": "http://example.com/new.jpg",
                "position": 1
            }
        }).encode("utf-8")
        mock_urlopen.return_value = mock_response

        image = Image(
            {"src": "http://example.com/new.jpg"},
            {"product_id": 123}
        )
        result = image.save()

        self.assertTrue(result)
        self.assertEqual(200, image.id)

    @patch("shopify_api.resource.urlopen")
    def test_image_destroy(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = b""
        mock_urlopen.return_value = mock_response

        image = Image({"id": 100}, {"product_id": 123})
        result = image.destroy()

        self.assertTrue(result)

        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        self.assertEqual("DELETE", request.method)


if __name__ == "__main__":
    unittest.main()
