"""
src/brokerage_statements/processors/charlesschwab/activity/corporate_actions.py

Corporate-action parsing for Charles Schwab account activity.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
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

_CASH_IN_LIEU_PATTERN = re.compile(
    r"^Cash-In-Lieu\s+"
    r"(?P<symbol>[A-Z][A-Z0-9.-]*)\s+"
    r"(?P<description>.+?)\s+"
    r"(?P<amount>[\d,]+(?:\.\d+)?)$"
)

_ADJUST_POSITION_PATTERN = re.compile(
    r"^AdjustPosition\s+"
    r"(?P<symbol>[A-Z][A-Z0-9.-]*)\s+"
    r"(?P<description>.+?)\s+"
    r"\((?P<quantity>[\d,]+(?:\.\d+)?)\)\s+"
    r"(?P<amount>[\d,]+(?:\.\d+)?)$"
)

_REVERSE_SPLIT_REMOVAL_SYMBOLS = {
    "AGEAGLEAERIALSYSINXXX": "UAVS",
}


@dataclass(frozen=True, slots=True)
class CorporateActionMatch:
    """One parsed corporate action and number of consumed rows."""

    event: CorporateActionEvent
    consumed_rows: int


def parse_corporate_action(  # noqa: PLR0911
    rows: tuple[ActivityRow, ...],
    evidence: tuple[SourceEvidence, ...],
    *,
    year: int,
) -> CorporateActionMatch | None:
    """Parse a supported Charles Schwab corporate action."""
    if not rows:
        return None

    first = rows[0]

    if first.category == "Redemption":
        return _parse_cash_in_lieu(
            first,
            evidence=evidence[:1],
            year=year,
        )

    if first.category != "Other Activity":
        return None

    body = _activity_body(first)

    if body.startswith("AdjustPosition "):
        return _parse_position_adjustment(
            first,
            evidence=evidence[:1],
            year=year,
        )

    if not body.startswith("ReverseSplit "):
        return None

    receipt_match = _REVERSE_SPLIT_RECEIPT_PATTERN.match(
        body,
    )

    if receipt_match is not None:
        return _parse_paired_reverse_split(
            rows,
            receipt_match=receipt_match,
            evidence=evidence,
            year=year,
        )

    removal_match = _REVERSE_SPLIT_REMOVAL_PATTERN.match(
        body,
    )

    if removal_match is not None:
        return _parse_removal_only_reverse_split(
            first,
            removal_match=removal_match,
            evidence=evidence[:1],
            year=year,
        )

    msg = f"Unable to parse Charles Schwab reverse split row: {first.text}"
    raise UnknownActivityError(msg)


def _parse_paired_reverse_split(
    rows: tuple[ActivityRow, ...],
    *,
    receipt_match: re.Match[str],
    evidence: tuple[SourceEvidence, ...],
    year: int,
) -> CorporateActionMatch:
    """Parse Schwab receipt/removal reverse-split rows."""
    receipt = rows[0]

    if len(rows) < 2:  # noqa: PLR2004
        msg = (
            "Charles Schwab reverse split is missing its paired row: "
            f"{receipt.text}"
        )
        raise UnknownActivityError(msg)

    removal = rows[1]

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

    removal_match = _REVERSE_SPLIT_REMOVAL_PATTERN.match(
        _activity_body(removal),
    )

    if removal_match is None:
        msg = (
            "Unable to parse Charles Schwab reverse split rows: "
            f"{receipt.text} | {removal.text}"
        )
        raise UnknownActivityError(msg)

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
            quantity_before=parse_unsigned_decimal(
                removal_match.group("quantity"),
            ),
            quantity_after=parse_unsigned_decimal(
                receipt_match.group("quantity"),
            ),
            evidence=evidence[:2],
        ),
        consumed_rows=2,
    )


def _parse_removal_only_reverse_split(
    row: ActivityRow,
    *,
    removal_match: re.Match[str],
    evidence: tuple[SourceEvidence, ...],
    year: int,
) -> CorporateActionMatch:
    """Parse a reverse split reporting only removed whole shares."""
    description = removal_match.group("description")

    try:
        symbol = _REVERSE_SPLIT_REMOVAL_SYMBOLS[description]
    except KeyError as exc:
        msg = (
            "Unknown Charles Schwab reverse split security description: "
            f"{description}"
        )
        raise UnknownActivityError(msg) from exc

    return CorporateActionMatch(
        event=CorporateActionEvent(
            date=parse_activity_date(
                row.date,
                year=year,
            ),
            action_type=CorporateActionType.REVERSE_SPLIT,
            source_security=SymbolSecurity(
                symbol,
            ),
            quantity_before=parse_unsigned_decimal(
                removal_match.group("quantity"),
            ),
            quantity_after=None,
            evidence=evidence,
        ),
        consumed_rows=1,
    )


def _parse_cash_in_lieu(
    row: ActivityRow,
    *,
    evidence: tuple[SourceEvidence, ...],
    year: int,
) -> CorporateActionMatch | None:
    """Parse Schwab cash paid instead of a fractional security."""
    match = _CASH_IN_LIEU_PATTERN.match(
        _activity_body(row),
    )

    if match is None:
        return None

    return CorporateActionMatch(
        event=CorporateActionEvent(
            date=parse_activity_date(
                row.date,
                year=year,
            ),
            action_type=CorporateActionType.CASH_IN_LIEU,
            source_security=SymbolSecurity(
                match.group("symbol"),
            ),
            cash=parse_unsigned_decimal(
                match.group("amount"),
            ),
            evidence=evidence,
        ),
        consumed_rows=1,
    )


def _parse_position_adjustment(
    row: ActivityRow,
    *,
    evidence: tuple[SourceEvidence, ...],
    year: int,
) -> CorporateActionMatch:
    """Parse a Schwab position-removal adjustment."""
    match = _ADJUST_POSITION_PATTERN.match(
        _activity_body(row),
    )

    if match is None:
        msg = (
            "Unable to parse Charles Schwab position adjustment row: "
            f"{row.text}"
        )
        raise UnknownActivityError(msg)

    amount = parse_unsigned_decimal(
        match.group("amount"),
    )

    if amount != Decimal("0"):
        msg = (
            "Charles Schwab position adjustment has unexpected "
            f"cash amount {amount}: {row.text}"
        )
        raise UnknownActivityError(msg)

    return CorporateActionMatch(
        event=CorporateActionEvent(
            date=parse_activity_date(
                row.date,
                year=year,
            ),
            action_type=CorporateActionType.POSITION_ADJUSTMENT,
            source_security=SymbolSecurity(
                match.group("symbol"),
            ),
            quantity_before=parse_unsigned_decimal(
                match.group("quantity"),
            ),
            quantity_after=Decimal("0"),
            evidence=evidence,
        ),
        consumed_rows=1,
    )


def _activity_body(
    row: ActivityRow,
) -> str:
    """Return activity text without normalized date and category."""
    prefix = f"{row.date} {row.category} "
    return row.text.removeprefix(prefix)
