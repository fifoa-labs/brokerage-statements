"""
tests/domain/test_securities.py

Tests for broker-neutral security identity models.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from brokerage_statements.domain import (
    OptionRight,
    OptionSecurity,
    SymbolSecurity,
)


def test_symbol_security_normalizes_symbol() -> None:
    """Symbol securities should normalize whitespace and case."""
    security = SymbolSecurity(symbol="  aapl  ")

    assert security.symbol == "AAPL"


def test_symbol_security_rejects_empty_symbol() -> None:
    """Symbol securities should require a symbol."""
    with pytest.raises(
        ValueError,
        match="symbol must not be empty",
    ):
        SymbolSecurity(symbol="   ")


def test_option_security_preserves_identity() -> None:
    """Option contracts should preserve normalized identity."""
    security = OptionSecurity(
        underlying=" snap ",
        expiration=date(2020, 8, 21),
        right=OptionRight.CALL,
        strike=Decimal("25"),
    )

    assert security.underlying == "SNAP"
    assert security.expiration == date(2020, 8, 21)
    assert security.right is OptionRight.CALL
    assert security.strike == Decimal("25")


def test_option_security_rejects_empty_underlying() -> None:
    """Option contracts should require an underlying symbol."""
    with pytest.raises(
        ValueError,
        match="underlying must not be empty",
    ):
        OptionSecurity(
            underlying=" ",
            expiration=date(2020, 8, 21),
            right=OptionRight.PUT,
            strike=Decimal("25"),
        )


@pytest.mark.parametrize(
    "strike",
    [
        Decimal("0"),
        Decimal("-1"),
    ],
)
def test_option_security_rejects_non_positive_strike(
    strike: Decimal,
) -> None:
    """Option strike prices should be positive."""
    with pytest.raises(
        ValueError,
        match="strike must be greater than zero",
    ):
        OptionSecurity(
            underlying="SNAP",
            expiration=date(2020, 8, 21),
            right=OptionRight.CALL,
            strike=strike,
        )


@pytest.mark.parametrize(
    "strike",
    [
        Decimal("NaN"),
        Decimal("Infinity"),
        Decimal("-Infinity"),
    ],
)
def test_option_security_rejects_non_finite_strike(
    strike: Decimal,
) -> None:
    """Option strike prices should be finite."""
    with pytest.raises(
        ValueError,
        match="strike must be finite",
    ):
        OptionSecurity(
            underlying="SNAP",
            expiration=date(2020, 8, 21),
            right=OptionRight.CALL,
            strike=strike,
        )
