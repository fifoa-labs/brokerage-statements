"""
src/brokerage_statements/processors/charlesschwab/sections.py

Structural section discovery for Charles Schwab monthly statements.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from brokerage_statements.text import StatementPage, StatementText


@dataclass(frozen=True, slots=True)
class StatementSections:
    """Pages containing known Charles Schwab statement sections."""

    summary: tuple[StatementPage, ...]
    positions: tuple[StatementPage, ...]
    transaction_summary: tuple[StatementPage, ...]
    transaction_details: tuple[StatementPage, ...]


def extract_sections(
    text: StatementText,
) -> StatementSections:
    """Locate known Charles Schwab monthly statement sections."""
    summary = _pages_containing(
        text,
        "Account Summary",
    )

    positions_start = _first_page_index(
        text,
        "Positions - Summary",
    )
    transactions_start = _first_page_index(
        text,
        "Transactions - Summary",
    )

    if not summary:
        msg = "Charles Schwab Account Summary section not found."
        raise ValueError(msg)

    if positions_start is None:
        msg = "Charles Schwab Positions - Summary section not found."
        raise ValueError(msg)

    if transactions_start is None:
        msg = "Charles Schwab Transactions - Summary section not found."
        raise ValueError(msg)

    if transactions_start < positions_start:
        msg = (
            "Charles Schwab Transactions - Summary section occurs "
            "before Positions - Summary."
        )
        raise ValueError(msg)

    positions = text.pages[positions_start : transactions_start + 1]

    transaction_summary = _pages_containing(
        text,
        "Transactions - Summary",
    )

    transaction_details = _transaction_detail_pages(
        text,
    )

    return StatementSections(
        summary=summary,
        positions=positions,
        transaction_summary=transaction_summary,
        transaction_details=transaction_details,
    )


def _pages_containing(
    text: StatementText,
    marker: str,
) -> tuple[StatementPage, ...]:
    """Return pages containing a structural marker."""
    return tuple(page for page in text.pages if marker in page.text)


def _first_page_index(
    text: StatementText,
    marker: str,
) -> int | None:
    """Return the index of the first page containing a marker."""
    for index, page in enumerate(text.pages):
        if marker in page.text:
            return index

    return None


def _transaction_detail_pages(
    text: StatementText,
) -> tuple[StatementPage, ...]:
    """Return pages spanning the optional transaction-detail section."""
    start = _first_page_index(
        text,
        "Transaction Details",
    )

    if start is None:
        return ()

    terms = _first_page_index_after(
        text,
        "Terms and Conditions",
        start=start,
    )

    if terms is None:
        return text.pages[start:]

    return text.pages[start : terms + 1]


def _first_page_index_after(
    text: StatementText,
    marker: str,
    *,
    start: int,
) -> int | None:
    """Return the first matching page index at or after a position."""
    for index in range(
        start,
        len(text.pages),
    ):
        if marker in text.pages[index].text:
            return index

    return None
