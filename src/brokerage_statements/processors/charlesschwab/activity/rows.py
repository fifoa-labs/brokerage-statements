"""
src/brokerage_statements/processors/charlesschwab/activity/rows.py

Logical row extraction for Charles Schwab transaction details.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from brokerage_statements.processors.charlesschwab.sections import (
        StatementSections,
    )
    from brokerage_statements.text import StatementPage


_DATE_PATTERN = re.compile(
    r"^(?P<date>\d{2}/\d{2})\s+(?P<rest>.+)$",
)

_TRANSACTION_END_MARKERS = (
    "TotalTransactions",
    "Total Transactions",
    "Datecolumnrepresents",
    "Date column represents",
    "Terms and Conditions",
)

_CATEGORY_PREFIXES = (
    "Deposit",
    "Withdrawal",
    "Buy",
    "Sell",
    "Dividend",
    "Interest",
    "Fee",
    "Redemption",
    "Other",
)

_HEADER_LINES = frozenset(
    {
        "Symbol/",
        "CUSIP Description Quantity",
        "Price/Rate",
        "perShare($)",
        "per Share($)",
        "Charges/",
        "Interest($) Amount($)",
        "Realized",
        "Gain/(Loss)($)",
    }
)


@dataclass(frozen=True, slots=True)
class ActivityRow:
    """One logical Schwab transaction row and its source location."""

    page_number: int
    sequence: int
    date: str
    category: str
    text: str


@dataclass(slots=True)
class _RowState:
    """Mutable extraction state spanning physical statement pages."""

    in_details: bool = False
    current_date: str | None = None
    current_category: str | None = None
    current_page: int | None = None
    current_parts: list[str] = field(default_factory=list)

    def clear_row(self) -> None:
        """Clear current row data while preserving inherited date."""
        self.current_category = None
        self.current_page = None
        self.current_parts.clear()

    def reset(self) -> None:
        """Clear all transaction-detail extraction state."""
        self.in_details = False
        self.current_date = None
        self.clear_row()


_RawActivityRow = tuple[int, str, str, str]


def extract_activity_rows(
    sections: StatementSections,
) -> tuple[ActivityRow, ...]:
    """Reconstruct logical rows from Schwab transaction details."""
    extracted: list[_RawActivityRow] = []
    state = _RowState()

    for page in sections.transaction_details:
        _consume_page(
            page,
            state=state,
            extracted=extracted,
        )

    _flush_current(
        state,
        extracted=extracted,
    )

    return _build_activity_rows(extracted)


def _consume_page(
    page: StatementPage,
    *,
    state: _RowState,
    extracted: list[_RawActivityRow],
) -> None:
    """Consume physical transaction-detail lines from one page."""
    for raw_line in page.text.splitlines():
        should_stop = _consume_line(
            raw_line.strip(),
            page_number=page.number,
            state=state,
            extracted=extracted,
        )

        if should_stop:
            return


def _consume_line(  # noqa: PLR0911
    line: str,
    *,
    page_number: int,
    state: _RowState,
    extracted: list[_RawActivityRow],
) -> bool:
    """Consume one physical line and return whether the section ended."""
    if line == "Transaction Details":
        state.in_details = True
        return False

    if not state.in_details:
        return False

    if _is_header_line(line):
        return False

    if _is_transaction_end(line):
        _flush_current(
            state,
            extracted=extracted,
        )
        state.reset()
        return True

    date_match = _DATE_PATTERN.match(line)

    if date_match is not None:
        _start_dated_row(
            date_match,
            page_number=page_number,
            state=state,
            extracted=extracted,
        )
        return False

    category, remainder = _split_category(line)

    if category is not None:
        _start_inherited_row(
            category,
            remainder,
            page_number=page_number,
            state=state,
            extracted=extracted,
        )
        return False

    if state.current_category is None:
        return False

    if _consume_other_activity_continuation(
        line,
        state=state,
    ):
        return False

    state.current_parts.append(line)
    return False


def _start_dated_row(
    match: re.Match[str],
    *,
    page_number: int,
    state: _RowState,
    extracted: list[_RawActivityRow],
) -> None:
    """Start a logical row containing an explicit transaction date."""
    _flush_current(
        state,
        extracted=extracted,
    )

    state.current_date = match.group("date")
    state.current_page = page_number

    category, remainder = _split_category(
        match.group("rest"),
    )

    if category is None:
        msg = (
            "Unrecognized Charles Schwab transaction category: "
            f"{match.group(0)}"
        )
        raise ValueError(msg)

    category, remainder = _normalize_other_activity(
        category,
        remainder,
    )

    state.current_category = category

    if remainder:
        state.current_parts.append(remainder)


def _start_inherited_row(
    category: str,
    remainder: str,
    *,
    page_number: int,
    state: _RowState,
    extracted: list[_RawActivityRow],
) -> None:
    """Start a new row inheriting the preceding transaction date."""
    _flush_current(
        state,
        extracted=extracted,
    )

    if state.current_date is None:
        msg = (
            "Charles Schwab transaction row has no inherited "
            f"date: {category} {remainder}".rstrip()
        )
        raise ValueError(msg)

    category, remainder = _normalize_other_activity(
        category,
        remainder,
    )

    state.current_page = page_number
    state.current_category = category

    if remainder:
        state.current_parts.append(remainder)


def _consume_other_activity_continuation(
    line: str,
    *,
    state: _RowState,
) -> bool:
    """Consume a physical continuation of the Other Activity category."""
    if state.current_category != "Other":
        return False

    category, remainder = _normalize_other_activity(
        "Other",
        line,
    )

    if category == "Other":
        return False

    state.current_category = category

    if remainder:
        state.current_parts.append(remainder)

    return True


def _normalize_other_activity(
    category: str,
    remainder: str,
) -> tuple[str, str]:
    """Normalize Schwab's physically split Other Activity category."""
    if category != "Other":
        return category, remainder

    if remainder == "Activity":
        return "Other Activity", ""

    prefix = "Activity "

    if remainder.startswith(prefix):
        return (
            "Other Activity",
            remainder[len(prefix) :].strip(),
        )

    return category, remainder


def _flush_current(
    state: _RowState,
    *,
    extracted: list[_RawActivityRow],
) -> None:
    """Append and clear the current logical row when one exists."""
    _append_current(
        extracted,
        page_number=state.current_page,
        date=state.current_date,
        category=state.current_category,
        parts=state.current_parts,
    )
    state.clear_row()


def _append_current(
    extracted: list[_RawActivityRow],
    *,
    page_number: int | None,
    date: str | None,
    category: str | None,
    parts: list[str],
) -> None:
    """Append one completed logical transaction row."""
    if category is None:
        return

    if page_number is None or date is None:
        msg = "Incomplete Charles Schwab transaction row metadata."
        raise ValueError(msg)

    text = " ".join(parts).strip()

    if not text:
        msg = "Charles Schwab transaction row contains no activity text."
        raise ValueError(msg)

    extracted.append(
        (
            page_number,
            date,
            category,
            text,
        )
    )


def _build_activity_rows(
    extracted: list[_RawActivityRow],
) -> tuple[ActivityRow, ...]:
    """Build immutable normalized logical rows."""
    return tuple(
        ActivityRow(
            page_number=page_number,
            sequence=sequence,
            date=date,
            category=category,
            text=" ".join(  # noqa: FLY002
                (
                    date,
                    category,
                    text,
                )
            ),
        )
        for sequence, (
            page_number,
            date,
            category,
            text,
        ) in enumerate(
            extracted,
            start=1,
        )
    )


def _split_category(
    value: str,
) -> tuple[str | None, str]:
    """Split a physical line into transaction category and remainder."""
    for category in _CATEGORY_PREFIXES:
        if value == category:
            return category, ""

        prefix = f"{category} "

        if value.startswith(prefix):
            return (
                category,
                value[len(prefix) :],
            )

    return None, value


def _is_transaction_end(line: str) -> bool:
    """Return whether a line terminates transaction detail rows."""
    return any(line.startswith(marker) for marker in _TRANSACTION_END_MARKERS)


def _is_header_line(line: str) -> bool:
    """Return whether a line belongs to the transaction table header."""
    return line in _HEADER_LINES
