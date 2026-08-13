"""
src/brokerage_statements/processors/tdameritrade/activity/cash.py

Cash movement parsing for TD Ameritrade account activity.
"""

from __future__ import annotations

import re

from brokerage_statements.domain import (
    CashTransferEvent,
    CashTransferType,
    SourceEvidence,
)
from brokerage_statements.exceptions import UnknownActivityError

from ._utils import (
    money_values,
    parse_date,
)

_CASH_TRANSFER_PATTERN = re.compile(
    r"^(?P<trade_date>\d{2}/\d{2}/\d{2})\s+"
    r"(?P<settle_date>\d{2}/\d{2}/\d{2})\s+"
    r"(?P<account_type>Cash|Margin)"
    r"(?:\s+Journal)?\s+-\s+"
    r"Funds\s+(?P<direction>Deposited|Disbursed)\s+"
    r"(?P<body>.+)$",
)

_INTERNAL_JOURNAL_PATTERN = re.compile(
    r"^\d{2}/\d{2}/\d{2}\s+"
    r"\d{2}/\d{2}/\d{2}\s+"
    r"(?:Cash|Margin)\s+Journal\s+-\s+Other\s+",
)

_KNOWN_INTERNAL_JOURNAL_MARKERS = (
    "MOVE CASH BALANCE TO",
    "PURCHASE FDIC INSURED",
    "REDEMPTION FDIC INSURED",
    "TRANSFER FROM",
)


def is_known_internal_journal(row: str) -> bool:
    """Return whether a row is a known internal cash movement."""
    if _INTERNAL_JOURNAL_PATTERN.match(row) is None:
        return False

    return any(marker in row for marker in _KNOWN_INTERNAL_JOURNAL_MARKERS)


def parse_cash_transfer(
    row: str,
    evidence: SourceEvidence,
) -> CashTransferEvent | None:
    """Parse deposited or disbursed funds."""
    match = _CASH_TRANSFER_PATTERN.match(row)

    if match is None:
        return None

    amounts = money_values(
        match.group("body"),
    )

    if len(amounts) < 2:  # noqa: PLR2004
        msg = f"Unable to parse TD Ameritrade cash transfer row: {row}"
        raise UnknownActivityError(msg)

    transfer_type = (
        CashTransferType.DEPOSIT
        if match.group("direction") == "Deposited"
        else CashTransferType.WITHDRAWAL
    )

    return CashTransferEvent(
        date=parse_date(
            match.group("settle_date"),
        ),
        transfer_type=transfer_type,
        amount=abs(amounts[-2]),
        evidence=(evidence,),
    )
