"""
src/brokerage_statements/processors/charlesschwab/activity/transfers.py

Security-transfer parsing for Charles Schwab account activity.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from brokerage_statements.domain import (
    SecurityTransferDirection,
    SecurityTransferEvent,
    SourceEvidence,
    SymbolSecurity,
)
from brokerage_statements.exceptions import UnknownActivityError

from ._utils import (
    parse_activity_date,
    parse_unsigned_decimal,
)

if TYPE_CHECKING:
    from decimal import Decimal

    from .rows import ActivityRow

_ACCOUNT_TRANSFER_PATTERN = re.compile(
    r"^Account\s*Transfer\s+"
    r"(?P<symbol>[A-Z][A-Z0-9.-]*)\s+"
    r"(?P<body>.+)$"
)

_NUMBER_PATTERN = re.compile(r"(?<![\d,.])[\d,]+(?:\.\d+)?(?![\d.])")

_FOUR_DECIMAL_PATTERN = re.compile(r"^[\d,]+\.\d{4}$")

_THREE_DECIMAL_PATTERN = re.compile(r"^[\d,]+\.\d{3}$")


def parse_security_transfer(
    row: ActivityRow,
    evidence: SourceEvidence,
    *,
    year: int,
) -> SecurityTransferEvent | None:
    """Parse a security transferred into the Schwab account."""
    if row.category != "Other Activity":
        return None

    body = _activity_body(row)
    match = _ACCOUNT_TRANSFER_PATTERN.match(body)

    if match is None:
        return None

    quantity = _parse_transfer_quantity(
        match.group("body"),
        row=row,
    )

    return SecurityTransferEvent(
        date=parse_activity_date(
            row.date,
            year=year,
        ),
        security=SymbolSecurity(
            match.group("symbol"),
        ),
        direction=SecurityTransferDirection.IN,
        quantity=quantity,
        evidence=(evidence,),
    )


def _parse_transfer_quantity(
    body: str,
    *,
    row: ActivityRow,
) -> Decimal:
    """Parse the reported Schwab security-transfer quantity."""
    tokens = tuple(match.group(0) for match in _NUMBER_PATTERN.finditer(body))

    for token in tokens:
        if _FOUR_DECIMAL_PATTERN.fullmatch(token):
            return parse_unsigned_decimal(token)

    for index, token in enumerate(tokens):
        if not _THREE_DECIMAL_PATTERN.fullmatch(token):
            continue

        reconstructed = _reconstruct_split_quantity(
            token,
            tokens[index + 1 :],
        )

        if reconstructed is not None:
            return reconstructed

    msg = f"Unable to parse Charles Schwab security transfer row: {row.text}"
    raise UnknownActivityError(msg)


def _reconstruct_split_quantity(
    head: str,
    following: tuple[str, ...],
) -> Decimal | None:
    """Reconstruct a four-decimal quantity split by PDF extraction."""
    for token in following:
        if len(token) != 1 or not token.isdigit():
            continue

        return parse_unsigned_decimal(
            f"{head}{token}",
        )

    return None


def _activity_body(
    row: ActivityRow,
) -> str:
    """Return activity text without normalized date and category."""
    prefix = f"{row.date} {row.category} "
    return row.text.removeprefix(prefix)
