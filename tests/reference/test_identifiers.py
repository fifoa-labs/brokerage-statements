"""
tests/reference/test_identifiers.py

Tests for brokerage security identifier resolution.
"""

from __future__ import annotations

import pytest

from brokerage_statements.exceptions import UnresolvedSecurityError
from brokerage_statements.reference import resolve_symbol


@pytest.mark.parametrize(
    ("identifier", "expected"),
    [
        ("AAPL", "AAPL"),
        (" uso ", "USO"),
        ("BRK.B", "BRK.B"),
    ],
)
def test_resolve_symbol_preserves_symbol_identity(
    identifier: str,
    expected: str,
) -> None:
    """Normal ticker symbols should normalize directly."""
    assert resolve_symbol(identifier) == expected


@pytest.mark.parametrize(
    ("identifier", "expected"),
    [
        ("91232N108", "USO"),
        ("91232N207", "USO"),
        ("25460E166", "JNUG"),
        ("25460G831", "JNUG"),
        ("98420U604", "XSPA"),
        ("98420U703", "XSPA"),
        ("Y73760301", "SHIP"),
        ("Y73760194", "SHIP"),
    ],
)
def test_resolve_symbol_resolves_known_cusip(
    identifier: str,
    expected: str,
) -> None:
    """Known CUSIPs should resolve to canonical symbols."""
    assert resolve_symbol(identifier) == expected


def test_resolve_symbol_rejects_unknown_cusip() -> None:
    """Unknown CUSIPs should fail rather than become symbols."""
    with pytest.raises(
        UnresolvedSecurityError,
        match="Unresolved security identifier",
    ):
        resolve_symbol("12345A678")


def test_resolve_symbol_rejects_empty_identifier() -> None:
    """Security identifiers should not be empty."""
    with pytest.raises(
        UnresolvedSecurityError,
        match="security identifier must not be empty",
    ):
        resolve_symbol(" ")


@pytest.mark.parametrize(
    "identifier",
    [
        "ABC DEF",
        "$AAPL",
        "@TEST",
    ],
)
def test_resolve_symbol_rejects_invalid_identifier(
    identifier: str,
) -> None:
    """Malformed identifiers should fail explicitly."""
    with pytest.raises(
        UnresolvedSecurityError,
        match="Invalid security identifier",
    ):
        resolve_symbol(identifier)
