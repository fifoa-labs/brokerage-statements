"""
src/brokerage_statements/processors/tdameritrade/activity/transfers.py

Security transfer parsing for TD Ameritrade account activity.
"""

from __future__ import annotations

import re

from brokerage_statements.domain import (
    SecurityTransferDirection,
    SecurityTransferEvent,
    SourceEvidence,
    SymbolSecurity,
)
from brokerage_statements.exceptions import UnknownActivityError
from brokerage_statements.reference import resolve_symbol

from ._utils import (
    parse_date,
    parse_unsigned_decimal,
)

_SECURITY_TRANSFER_PATTERN = re.compile(
    r"^(?P<trade_date>\d{2}/\d{2}/\d{2})\s+"
    r"(?P<settle_date>\d{2}/\d{2}/\d{2})\s+"
    r"(?P<account_type>Cash|Margin)\s+"
    r"(?P<direction>Received|Delivered)\s+-\s+Other\s+"
    r"(?P<body>.+)$",
)

_SECURITY_TRANSFER_VALUES_PATTERN = re.compile(
    r"\b(?P<identifier>[A-Z0-9][A-Z0-9.-]*)\s+"
    r"(?P<quantity>[\d,]+(?:\.\d+)?)-?\s+"
    r"\$?\s*0\.00\b",
)

_KNOWN_INTERNAL_SECURITY_TRANSFER_MARKERS = (
    "TRANSFER FROM ",
    "TRANSFER TO ",
)


def is_known_internal_security_transfer(
    row: str,
) -> bool:
    """Return whether a security transfer stays inside the TD account."""
    match = _SECURITY_TRANSFER_PATTERN.match(row)

    if match is None:
        return False

    body = match.group("body")

    return any(
        marker in body for marker in _KNOWN_INTERNAL_SECURITY_TRANSFER_MARKERS
    )


def parse_security_transfer(
    row: str,
    evidence: SourceEvidence,
) -> SecurityTransferEvent | None:
    """Parse a security delivered into or out of the account."""
    match = _SECURITY_TRANSFER_PATTERN.match(row)

    if match is None:
        return None

    values = _SECURITY_TRANSFER_VALUES_PATTERN.search(
        match.group("body"),
    )

    if values is None:
        msg = f"Unable to parse TD Ameritrade security transfer row: {row}"
        raise UnknownActivityError(msg)

    direction = (
        SecurityTransferDirection.IN
        if match.group("direction") == "Received"
        else SecurityTransferDirection.OUT
    )

    return SecurityTransferEvent(
        date=parse_date(
            match.group("settle_date"),
        ),
        security=SymbolSecurity(
            resolve_symbol(
                values.group("identifier"),
            )
        ),
        direction=direction,
        quantity=parse_unsigned_decimal(
            values.group("quantity"),
        ),
        evidence=(evidence,),
    )
