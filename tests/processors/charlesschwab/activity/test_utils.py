"""
tests/processors/charlesschwab/activity/test_utils.py

Tests for Charles Schwab activity parsing utilities.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from brokerage_statements.processors.charlesschwab.activity._utils import (
    parse_activity_date,
    parse_unsigned_decimal,
)


def test_parse_activity_date_preserves_statement_year() -> None:
    """Schwab month/day dates should use the statement year."""
    assert parse_activity_date(
        "11/06",
        year=2023,
    ) == date(2023, 11, 6)


def test_parse_unsigned_decimal_removes_grouping_commas() -> None:
    """Schwab decimal notation should normalize grouping commas."""
    assert parse_unsigned_decimal("2,000,000.0000") == Decimal("2000000.0000")


def test_parse_unsigned_decimal_returns_positive_value() -> None:
    """Unsigned Schwab values should normalize negative notation."""
    assert parse_unsigned_decimal("-10.25") == Decimal("10.25")
