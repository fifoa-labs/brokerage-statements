"""
src/brokerage_statements/processors/charlesschwab/activity/income.py

Income parsing for Charles Schwab account activity.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from brokerage_statements.domain import (
    IncomeEvent,
    IncomeType,
    SourceEvidence,
)
from brokerage_statements.exceptions import UnknownActivityError

from ._utils import (
    parse_activity_date,
    parse_unsigned_decimal,
)

if TYPE_CHECKING:
    from .rows import ActivityRow

_INTEREST_PATTERN = re.compile(
    r"^Credit\s*Interest\s+"
    r"(?P<description>.+?)\s+"
    r"(?P<amount>[\d,]+(?:\.\d+)?)$"
)


def parse_income(
    row: ActivityRow,
    evidence: SourceEvidence,
    *,
    year: int,
) -> IncomeEvent | None:
    """Parse supported Charles Schwab income activity."""
    if row.category != "Interest":
        return None

    body = _activity_body(row)
    match = _INTEREST_PATTERN.match(body)

    if match is None:
        msg = f"Unable to parse Charles Schwab interest row: {row.text}"
        raise UnknownActivityError(msg)

    return IncomeEvent(
        date=parse_activity_date(
            row.date,
            year=year,
        ),
        income_type=IncomeType.INTEREST,
        amount=parse_unsigned_decimal(
            match.group("amount"),
        ),
        evidence=(evidence,),
    )


def _activity_body(
    row: ActivityRow,
) -> str:
    """Return activity text without normalized date and category."""
    prefix = f"{row.date} {row.category} "
    return row.text.removeprefix(prefix)
