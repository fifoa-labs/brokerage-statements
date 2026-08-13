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
    parse_unsigned_decimal,
)

_INCOME_PATTERN = re.compile(
    r"^(?P<trade_date>\d{2}/\d{2}/\d{2})\s+"
    r"(?P<settle_date>\d{2}/\d{2}/\d{2})\s+"
    r"(?P<account_type>Cash|Margin)\s+"
    r"Div/Int\s+-\s+Income\s+"
    r"(?P<body>.+)$",
)

_INSURED_DEPOSIT_INTEREST_PATTERN = re.compile(
    r"^(?P<trade_date>\d{2}/\d{2}/\d{2})\s+"
    r"(?P<settle_date>\d{2}/\d{2}/\d{2})\s+"
    r"(?P<account_type>Cash|Margin)\s+"
    r"Div/Int\s+-\s+Other\s+"
    r"FDIC INSURED DEPOSIT MMDA1\s+-\s+"
    r"0\.00\s+"
    r"(?P<amount>[\d,]+(?:\.\d+)?)\s+"
    r"(?P<balance>\(?[\d,]+(?:\.\d+)?\)?)\s+"
    r"(?P<annotation>.+)$",
)


def parse_income(
    row: str,
    evidence: SourceEvidence,
) -> IncomeEvent | None:
    """Parse TD Ameritrade interest income."""
    match = _INCOME_PATTERN.match(row)

    if match is not None:
        return _parse_income_match(
            match,
            row,
            evidence,
        )

    insured_deposit = _INSURED_DEPOSIT_INTEREST_PATTERN.match(row)

    if insured_deposit is None:
        return None

    annotation = insured_deposit.group("annotation")

    if (
        "Interest: Insured Deposit Account" not in annotation
        and "Insured Deposit Account Interest" not in annotation
    ):
        return None

    return IncomeEvent(
        date=parse_date(
            insured_deposit.group("settle_date"),
        ),
        income_type=IncomeType.INTEREST,
        amount=parse_unsigned_decimal(
            insured_deposit.group("amount"),
        ),
        evidence=(evidence,),
    )


def _parse_income_match(
    match: re.Match[str],
    row: str,
    evidence: SourceEvidence,
) -> IncomeEvent:
    """Normalize a matched standard TD Ameritrade income row."""
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
