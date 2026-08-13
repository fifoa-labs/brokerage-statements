"""
src/brokerage_statements/processors/tdameritrade/activity/_utils.py

Shared parsing utilities for TD Ameritrade account activity.
"""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal

_MONEY_PATTERN = re.compile(r"\$?\s*(?P<value>\(?[\d,]+(?:\.\d+)?\)?)")


def money_values(value: str) -> tuple[Decimal, ...]:
    """Return monetary values appearing in source order."""
    return tuple(
        parse_decimal(match.group("value"))
        for match in _MONEY_PATTERN.finditer(value)
    )


def parse_unsigned_decimal(value: str) -> Decimal:
    """Parse a decimal magnitude regardless of statement sign notation."""
    return abs(parse_decimal(value))


def parse_decimal(value: str) -> Decimal:
    """Parse TD Ameritrade money and quantity notation."""
    normalized = value.strip().replace("$", "").replace(",", "")

    negative = normalized.startswith("(") and normalized.endswith(")")

    if negative:
        normalized = normalized[1:-1]

    result = Decimal(normalized)

    if negative:
        return -result

    return result


def parse_date(value: str) -> date:
    """Parse a TD Ameritrade two-digit activity date."""
    month_text, day_text, year_text = value.split("/")

    return date(
        year=2000 + int(year_text),
        month=int(month_text),
        day=int(day_text),
    )
