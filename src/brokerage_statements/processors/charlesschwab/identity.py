"""
src/brokerage_statements/processors/charlesschwab/identity.py

Identity extraction for Charles Schwab monthly statements.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from brokerage_statements.text import StatementText


_ACCOUNT_PATTERN = re.compile(
    r"\b(?P<account>\d{4}-\d{4})\b",
)

_PERIOD_PATTERN = re.compile(
    r"(?P<month>"
    r"January|February|March|April|May|June|July|August|"
    r"September|October|November|December"
    r")\s*"
    r"(?P<start_day>\d{1,2})\s*-\s*"
    r"(?P<end_day>\d{1,2})\s*,\s*"
    r"(?P<year>\d{4})"
)

_MONTHS = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12,
}


@dataclass(frozen=True, slots=True)
class StatementIdentity:
    """Charles Schwab statement identity."""

    account_id: str
    start: date
    end: date


def parse_statement_identity(
    text: StatementText,
) -> StatementIdentity:
    """Extract account identity and statement period."""
    first_page = text.pages[0].text

    account_match = _ACCOUNT_PATTERN.search(first_page)

    if account_match is None:
        msg = "Charles Schwab account number not found."
        raise ValueError(msg)

    period_match = _PERIOD_PATTERN.search(first_page)

    if period_match is None:
        msg = "Charles Schwab statement period not found."
        raise ValueError(msg)

    year = int(period_match.group("year"))
    month = _MONTHS[period_match.group("month")]

    return StatementIdentity(
        account_id=account_match.group("account"),
        start=date(
            year=year,
            month=month,
            day=int(period_match.group("start_day")),
        ),
        end=date(
            year=year,
            month=month,
            day=int(period_match.group("end_day")),
        ),
    )
