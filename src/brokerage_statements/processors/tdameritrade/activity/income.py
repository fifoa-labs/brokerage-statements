"""
src/brokerage_statements/processors/tdameritrade/activity/income.py

Income parsing for TD Ameritrade account activity.
"""

from __future__ import annotations

import re

from brokerage_statements.domain import (
    IncomeEvent,
    IncomeType,
    SourceEvidence,
)
from brokerage_statements.exceptions import UnknownActivityError

from ._utils import (
    money_values,
    parse_date,
)

_INCOME_PATTERN = re.compile(
    r"^(?P<trade_date>\d{2}/\d{2}/\d{2})\s+"
    r"(?P<settle_date>\d{2}/\d{2}/\d{2})\s+"
    r"(?P<account_type>Cash|Margin)\s+"
    r"Div/Int\s+-\s+Income\s+"
    r"(?P<body>.+)$",
)


def parse_income(
    row: str,
    evidence: SourceEvidence,
) -> IncomeEvent | None:
    """Parse brokerage interest income."""
    match = _INCOME_PATTERN.match(row)

    if match is None:
        return None

    amounts = money_values(
        match.group("body"),
    )

    if len(amounts) < 2:  # noqa: PLR2004
        msg = f"Unable to parse TD Ameritrade income row: {row}"
        raise UnknownActivityError(msg)

    return IncomeEvent(
        date=parse_date(
            match.group("settle_date"),
        ),
        income_type=IncomeType.INTEREST,
        amount=abs(amounts[-2]),
        evidence=(evidence,),
    )
