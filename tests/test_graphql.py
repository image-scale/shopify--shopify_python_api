"""Tests for GraphQL client."""

import json
import unittest
from unittest.mock import patch, MagicMock

from shopify_api import (
    ShopSession,
    ResourceBase,
    GraphQLClient,
    GraphQLError,
)


class TestGraphQLClient(unittest.TestCase):
    """Test GraphQL client."""

    def setUp(self):
        ResourceBase.clear_session()
        session = ShopSession("testshop", "2024-07", "token123")
        ResourceBase.activate_session(session)

    @patch("shopify_api.graphql.urlopen")
    def test_execute_simple_query(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "data": {
                "shop": {
                    "name": "Test Shop",
                    "id": "gid://shopify/Shop/12345"
                }
            }
        }).encode("utf-8")
        mock_urlopen.return_value = mock_response

        client = GraphQLClient()
        result = client.execute("{ shop { name id } }")

        parsed = json.loads(result)
        self.assertEqual("Test Shop", parsed["data"]["shop"]["name"])

    @patch("shopify_api.graphql.urlopen")
    def test_execute_with_variables(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "data": {
                "product": {
                    "id": "gid://shopify/Product/123",
                    "title": "Widget"
                }
            }
        }).encode("utf-8")
        mock_urlopen.return_value = mock_response

        client = GraphQLClient()
        query = """
            query GetProduct($id: ID!) {
                product(id: $id) {
                    id
                    title
                }
            }
        """
        variables = {"id": "gid://shopify/Product/123"}
        result = client.execute(query, variables=variables)

        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        body = json.loads(request.data.decode("utf-8"))
        self.assertEqual(variables, body["variables"])

    @patch("shopify_api.graphql.urlopen")
    def test_execute_with_operation_name(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "data": {"shop": {"name": "Test"}}
        }).encode("utf-8")
        mock_urlopen.return_value = mock_response

        client = GraphQLClient()
        query = """
            query GetShopName {
                shop { name }
            }
            query GetShopId {
                shop { id }
            }
        """
        result = client.execute(query, operation_name="GetShopName")

        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        body = json.loads(request.data.decode("utf-8"))
        self.assertEqual("GetShopName", body["operationName"])

    @patch("shopify_api.graphql.urlopen")
    def test_execute_json_returns_dict(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "data": {"shop": {"name": "Test Shop"}}
        }).encode("utf-8")
        mock_urlopen.return_value = mock_response

        client = GraphQLClient()
        result = client.execute_json("{ shop { name } }")

        self.assertIsInstance(result, dict)
        self.assertEqual("Test Shop", result["data"]["shop"]["name"])

    @patch("shopify_api.graphql.urlopen")
    def test_request_includes_auth_header(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"data": {}}'
        mock_urlopen.return_value = mock_response

        client = GraphQLClient()
        client.execute("{ shop { name } }")

        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        self.assertEqual("token123", request.get_header("X-shopify-access-token"))

    @patch("shopify_api.graphql.urlopen")
    def test_request_includes_content_type(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"data": {}}'
        mock_urlopen.return_value = mock_response

        client = GraphQLClient()
        client.execute("{ shop { name } }")

        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        self.assertEqual("application/json", request.get_header("Content-type"))

    def test_client_without_session_raises_error(self):
        ResourceBase.clear_session()

        with self.assertRaises(GraphQLError):
            GraphQLClient()

    @patch("shopify_api.graphql.urlopen")
    def test_http_error_raises_graphql_error(self, mock_urlopen):
        from urllib.error import HTTPError
        mock_urlopen.side_effect = HTTPError(
            url="", code=400, msg="Bad Request",
            hdrs={}, fp=MagicMock(read=lambda: b'{"errors": []}')
        )

        client = GraphQLClient()

        with self.assertRaises(GraphQLError):
            client.execute("invalid query")


if __name__ == "__main__":
    unittest.main()
