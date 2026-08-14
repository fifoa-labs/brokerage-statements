"""
src/brokerage_statements/processors/charlesschwab/activity/_utils.py

Shared parsing utilities for Charles Schwab account activity.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal


def parse_activity_date(
    value: str,
    *,
    year: int,
) -> date:
    """Parse a Schwab month/day activity date."""
    month_text, day_text = value.split("/")

    return date(
        year=year,
        month=int(month_text),
        day=int(day_text),
    )


def parse_unsigned_decimal(
    value: str,
) -> Decimal:
    """Parse a non-negative Schwab decimal value."""
    return abs(
        Decimal(
            value.replace(",", ""),
        )
    )
