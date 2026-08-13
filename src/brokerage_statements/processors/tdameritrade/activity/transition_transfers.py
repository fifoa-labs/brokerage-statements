"""
src/brokerage_statements/processors/tdameritrade/activity/transition_transfers.py

Transition security-transfer parsing for TD Ameritrade account activity.
"""

from __future__ import annotations

import re

from brokerage_statements.domain import (
    SecurityTransferDirection,
    SecurityTransferEvent,
    SourceEvidence,
    SymbolSecurity,
)
from brokerage_statements.reference import resolve_symbol

from ._utils import parse_date, parse_unsigned_decimal

_TRANSITION_SECURITY_TRANSFER_PATTERN = re.compile(
    r"^(?P<trade_date>\d{2}/\d{2}/\d{2})\s+"
    r"(?P<settle_date>\d{2}/\d{2}/\d{2})\s+"
    r"(?P<account_type>Cash|Margin)\s+"
    r"Delivered\s+-\s+"
    r"(?P<description>.+?)\s+"
    r"(?P<identifier>[A-Z0-9][A-Z0-9.-]*)\s+"
    r"(?P<quantity>[\d,]+(?:\.\d+)?)-\s+"
    r"\$?\s*0\.00\s+"
    r"\$?\s*-\s+"
    r"(?P<balance>\(?[\d,]+(?:\.\d+)?\)?)\s+"
    r"(?P<annotation>.+)$",
)

_TRANSITION_MARKER = "TDA TO CS&CO TRANSFER"


def parse_transition_security_transfer(
    row: str,
    evidence: SourceEvidence,
) -> SecurityTransferEvent | None:
    """Parse a security delivered during the TD-to-Schwab transition."""
    match = _TRANSITION_SECURITY_TRANSFER_PATTERN.match(row)

    if match is None:
        return None

    if _TRANSITION_MARKER not in match.group("annotation"):
        return None

    return SecurityTransferEvent(
        date=parse_date(
            match.group("settle_date"),
        ),
        security=SymbolSecurity(
            resolve_symbol(
                match.group("identifier"),
            )
        ),
        direction=SecurityTransferDirection.OUT,
        quantity=parse_unsigned_decimal(
            match.group("quantity"),
        ),
        evidence=(evidence,),
    )
