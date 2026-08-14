"""
src/brokerage_statements/processors/charlesschwab/activity/corporate_actions.py

Corporate-action parsing for Charles Schwab account activity.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from brokerage_statements.domain import (
    CorporateActionEvent,
    CorporateActionType,
    SourceEvidence,
    SymbolSecurity,
)
from brokerage_statements.exceptions import UnknownActivityError

from ._utils import (
    parse_activity_date,
    parse_unsigned_decimal,
)

if TYPE_CHECKING:
    from .rows import ActivityRow

_REVERSE_SPLIT_RECEIPT_PATTERN = re.compile(
    r"^ReverseSplit\s+"
    r"(?P<symbol>[A-Z][A-Z0-9.-]*)\s+"
    r"(?P<description>.+?)\s+"
    r"(?P<quantity>[\d,]+(?:\.\d+)?)$"
)

_REVERSE_SPLIT_REMOVAL_PATTERN = re.compile(
    r"^ReverseSplit\s+"
    r"(?P<description>.+?)\s+"
    r"\((?P<quantity>[\d,]+(?:\.\d+)?)\)"
    r"(?:\s+REVERSESPLIT)?$"
)


@dataclass(frozen=True, slots=True)
class CorporateActionMatch:
    """One parsed corporate action and number of consumed rows."""

    event: CorporateActionEvent
    consumed_rows: int


def parse_corporate_action(
    rows: tuple[ActivityRow, ...],
    evidence: tuple[SourceEvidence, ...],
    *,
    year: int,
) -> CorporateActionMatch | None:
    """Parse a grouped Charles Schwab corporate action."""
    if not rows:
        return None

    first = rows[0]

    if first.category != "Other Activity":
        return None

    first_body = _activity_body(first)

    if not first_body.startswith("ReverseSplit "):
        return None

    if len(rows) < 2:  # noqa: PLR2004
        msg = (
            "Charles Schwab reverse split is missing its paired row: "
            f"{first.text}"
        )
        raise UnknownActivityError(msg)

    second = rows[1]

    return _parse_reverse_split(
        first,
        second,
        evidence=evidence,
        year=year,
    )


def _parse_reverse_split(
    receipt: ActivityRow,
    removal: ActivityRow,
    *,
    evidence: tuple[SourceEvidence, ...],
    year: int,
) -> CorporateActionMatch:
    """Parse paired Schwab reverse-split receipt and removal rows."""
    if removal.date != receipt.date:
        msg = (
            "Charles Schwab reverse split rows have different dates: "
            f"{receipt.text} | {removal.text}"
        )
        raise UnknownActivityError(msg)

    if removal.category != "Other Activity":
        msg = (
            "Charles Schwab reverse split has unexpected paired row: "
            f"{removal.text}"
        )
        raise UnknownActivityError(msg)

    receipt_match = _REVERSE_SPLIT_RECEIPT_PATTERN.match(
        _activity_body(receipt),
    )
    removal_match = _REVERSE_SPLIT_REMOVAL_PATTERN.match(
        _activity_body(removal),
    )

    if receipt_match is None or removal_match is None:
        msg = (
            "Unable to parse Charles Schwab reverse split rows: "
            f"{receipt.text} | {removal.text}"
        )
        raise UnknownActivityError(msg)

    quantity_after = parse_unsigned_decimal(
        receipt_match.group("quantity"),
    )
    quantity_before = parse_unsigned_decimal(
        removal_match.group("quantity"),
    )

    return CorporateActionMatch(
        event=CorporateActionEvent(
            date=parse_activity_date(
                receipt.date,
                year=year,
            ),
            action_type=CorporateActionType.REVERSE_SPLIT,
            source_security=SymbolSecurity(
                receipt_match.group("symbol"),
            ),
            quantity_before=quantity_before,
            quantity_after=quantity_after,
            evidence=evidence,
        ),
        consumed_rows=2,
    )


def _activity_body(
    row: ActivityRow,
) -> str:
    """Return activity text without normalized date and category."""
    prefix = f"{row.date} {row.category} "
    return row.text.removeprefix(prefix)
