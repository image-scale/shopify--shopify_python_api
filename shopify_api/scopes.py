"""API access scope management for Shopify OAuth."""

import re


class ScopeFormatError(Exception):
    """Raised when a scope string has an invalid format."""
    pass


class ScopeSet:
    """Manages a set of OAuth permission scopes.

    Handles scope validation, compression (write implies read),
    and comparison operations.
    """

    DELIMITER = ","

    SCOPE_PATTERN = re.compile(
        r"^(?P<unauthenticated>unauthenticated_)?(write|read)_(?P<resource>\w+)$"
    )

    WRITE_PATTERN = re.compile(
        r"^(?P<unauthenticated>unauthenticated_)?write_(?P<resource>\w+)$"
    )

    def __init__(self, scopes):
        """Create a scope set from a string or list.

        Args:
            scopes: Either a comma-separated string or list of scope strings

        Raises:
            ScopeFormatError: If any scope has invalid format
        """
        if isinstance(scopes, str):
            scope_list = scopes.split(self.DELIMITER)
        else:
            scope_list = list(scopes)

        sanitized = frozenset(
            scope.strip() for scope in scope_list if scope.strip()
        )

        self._validate_scopes(sanitized)

        implied = frozenset(
            self._implied_read_scope(scope) for scope in sanitized
            if self._implied_read_scope(scope) is not None
        )

        self._compressed = sanitized - implied
        self._expanded = sanitized.union(implied)

    def _validate_scopes(self, scopes):
        """Validate that all scopes match the expected pattern.

        Args:
            scopes: Set of scope strings

        Raises:
            ScopeFormatError: If any scope is invalid
        """
        for scope in scopes:
            if not self.SCOPE_PATTERN.match(scope):
                raise ScopeFormatError(
                    f"'{scope}' is not a valid access scope"
                )

    def _implied_read_scope(self, scope):
        """Get the implied read scope for a write scope.

        Args:
            scope: A scope string

        Returns:
            The corresponding read scope if input is a write scope, None otherwise
        """
        match = self.WRITE_PATTERN.match(scope)
        if match:
            unauthenticated = match.group("unauthenticated") or ""
            resource = match.group("resource")
            return f"{unauthenticated}read_{resource}"
        return None

    def covers(self, other):
        """Check if this scope set covers another.

        A scope set covers another if all scopes in the other set
        are present in this set's expanded form.

        Args:
            other: Another ScopeSet to check

        Returns:
            True if this scope set covers the other
        """
        return other._compressed <= self._expanded

    def __str__(self):
        """Return comma-separated string of compressed scopes."""
        return self.DELIMITER.join(sorted(self._compressed))

    def __iter__(self):
        """Iterate over compressed scopes."""
        return iter(sorted(self._compressed))

    def __eq__(self, other):
        """Check equality based on compressed scopes."""
        if not isinstance(other, ScopeSet):
            return False
        return self._compressed == other._compressed

    def __repr__(self):
        return f"<ScopeSet: {self}>"

    def __len__(self):
        """Return number of compressed scopes."""
        return len(self._compressed)

    def __contains__(self, scope):
        """Check if a scope is in the expanded set."""
        return scope in self._expanded
