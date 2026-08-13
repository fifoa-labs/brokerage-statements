"""
src/brokerage_statements/processors/tdameritrade/activity/expenses.py

Expense parsing for TD Ameritrade account activity.
"""

from __future__ import annotations

import re

from brokerage_statements.domain import FeeEvent, SourceEvidence

from ._utils import parse_date, parse_unsigned_decimal

_MARGIN_INTEREST_PATTERN = re.compile(
    r"^(?P<trade_date>\d{2}/\d{2}/\d{2})\s+"
    r"(?P<settle_date>\d{2}/\d{2}/\d{2})\s+"
    r"(?P<account_type>Cash|Margin)\s+"
    r"Div/Int\s+-\s+Expense\s+"
    r"MARGIN INTEREST CHARGE\s+-\s+-\s+"
    r"0\.00\s+"
    r"(?P<amount>\(?[\d,]+(?:\.\d+)?\)?)\s+"
    r"(?P<balance>\(?[\d,]+(?:\.\d+)?\)?)"
    r"(?P<annotation>.*)$",
)


def parse_expense(
    row: str,
    evidence: SourceEvidence,
) -> FeeEvent | None:
    """Parse TD Ameritrade expense activity."""
    match = _MARGIN_INTEREST_PATTERN.match(row)

    if match is None:
        return None

    return FeeEvent(
        date=parse_date(
            match.group("settle_date"),
        ),
        amount=parse_unsigned_decimal(
            match.group("amount"),
        ),
        evidence=(evidence,),
        description="Margin Interest Charge",
    )
