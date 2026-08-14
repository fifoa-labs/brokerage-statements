"""
src/brokerage_statements/processors/charlesschwab/activity/cash.py

Cash-transfer parsing for Charles Schwab account activity.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from brokerage_statements.domain import (
    CashTransferEvent,
    CashTransferType,
    SourceEvidence,
)
from brokerage_statements.exceptions import UnknownActivityError

from ._utils import (
    parse_activity_date,
    parse_unsigned_decimal,
)

if TYPE_CHECKING:
    from .rows import ActivityRow

_ACCOUNT_TRANSFER_PATTERN = re.compile(
    r"^Account\s*Transfer\s+"
    r"(?P<description>.+?)\s+"
    r"(?P<amount>[\d,]+(?:\.\d+)?)$"
)

_TRANSITION_MARKER = "TDATOCS&COTRANSFER"


def _compact(value: str) -> str:
    """Return text with all whitespace removed."""
    return "".join(value.split())


def parse_cash_transfer(
    row: ActivityRow,
    evidence: SourceEvidence,
    *,
    year: int,
) -> CashTransferEvent | None:
    """Parse a supported incoming Schwab cash transfer."""
    if row.category != "Deposit":
        return None

    body = _activity_body(row)
    match = _ACCOUNT_TRANSFER_PATTERN.match(body)

    if match is None:
        msg = f"Unable to parse Charles Schwab deposit row: {row.text}"
        raise UnknownActivityError(msg)

    description = _compact(
        match.group("description"),
    )

    if _TRANSITION_MARKER not in description:
        return None

    return CashTransferEvent(
        date=parse_activity_date(
            row.date,
            year=year,
        ),
        transfer_type=CashTransferType.DEPOSIT,
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
