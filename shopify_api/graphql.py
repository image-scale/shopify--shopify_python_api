"""GraphQL client for Shopify API."""

import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from .resource import ResourceBase


class GraphQLError(Exception):
    """Raised when a GraphQL request fails."""
    pass


class GraphQLClient:
    """Client for executing GraphQL queries against Shopify.

    Uses the currently active session to authenticate requests.
    """

    def __init__(self):
        """Initialize the GraphQL client.

        Uses the site and headers from the active ResourceBase session.
        """
        site = ResourceBase.get_site()
        if not site:
            raise GraphQLError("No active session")

        self._endpoint = f"{site}/graphql.json"
        self._headers = ResourceBase.get_headers()

    def execute(self, query, variables=None, operation_name=None):
        """Execute a GraphQL query.

        Args:
            query: The GraphQL query or mutation string
            variables: Optional dict of variables to pass to the query
            operation_name: Optional name of the operation to execute
                          (for documents with multiple operations)

        Returns:
            The JSON response as a string

        Raises:
            GraphQLError: If the request fails
        """
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        headers.update(self._headers)

        payload = {
            "query": query,
        }

        if variables is not None:
            payload["variables"] = variables

        if operation_name is not None:
            payload["operationName"] = operation_name

        data = json.dumps(payload).encode("utf-8")
        request = Request(self._endpoint, data=data, headers=headers, method="POST")

        try:
            response = urlopen(request)
            return response.read().decode("utf-8")
        except HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else ""
            raise GraphQLError(f"GraphQL request failed: {e.code} - {error_body}")

    def execute_json(self, query, variables=None, operation_name=None):
        """Execute a GraphQL query and return parsed JSON.

        Args:
            query: The GraphQL query or mutation string
            variables: Optional dict of variables to pass to the query
            operation_name: Optional name of the operation to execute

        Returns:
            The response as a parsed dict/list

        Raises:
            GraphQLError: If the request fails or response is invalid JSON
        """
        response = self.execute(query, variables, operation_name)
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            raise GraphQLError(f"Invalid JSON response: {e}")
