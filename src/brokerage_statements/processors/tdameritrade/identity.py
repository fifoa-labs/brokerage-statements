"""
src/brokerage_statements/processors/tdameritrade/identity.py

Identity extraction for TD Ameritrade monthly statements.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from brokerage_statements.text import StatementText

_ACCOUNT_PATTERN = re.compile(
    r"Statement for Account #\s*(?P<account>[0-9-]+)",
)

_PERIOD_PATTERN = re.compile(
    r"Statement Reporting Period:\s*"
    r"(?P<start>\d{2}/\d{2}/\d{2})\s*-\s*"
    r"(?P<end>\d{2}/\d{2}/\d{2})",
)


@dataclass(frozen=True, slots=True)
class StatementIdentity:
    """TD Ameritrade statement identity."""

    account_id: str
    start: date
    end: date


def parse_statement_identity(
    text: StatementText,
) -> StatementIdentity:
    """Extract account identity and reporting period."""
    account_match = _ACCOUNT_PATTERN.search(text.text)

    if account_match is None:
        msg = "TD Ameritrade account number not found."
        raise ValueError(msg)

    period_match = _PERIOD_PATTERN.search(text.text)

    if period_match is None:
        msg = "TD Ameritrade statement reporting period not found."
        raise ValueError(msg)

    return StatementIdentity(
        account_id=account_match.group("account"),
        start=_parse_date(period_match.group("start")),
        end=_parse_date(period_match.group("end")),
    )


def _parse_date(value: str) -> date:
    """Parse a TD Ameritrade two-digit statement date."""
    month_text, day_text, year_text = value.split("/")

    return date(
        year=2000 + int(year_text),
        month=int(month_text),
        day=int(day_text),
    )
