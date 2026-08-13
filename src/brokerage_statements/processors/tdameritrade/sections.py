"""
src/brokerage_statements/processors/tdameritrade/sections.py

Structural section discovery for TD Ameritrade monthly statements.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from brokerage_statements.text import StatementPage, StatementText


@dataclass(frozen=True, slots=True)
class StatementSections:
    """Pages containing known TD Ameritrade statement sections."""

    summary: tuple[StatementPage, ...]
    positions: tuple[StatementPage, ...]
    activity: tuple[StatementPage, ...]
    pending: tuple[StatementPage, ...]


def extract_sections(
    text: StatementText,
) -> StatementSections:
    """Locate known TD Ameritrade statement sections."""
    summary = _pages_containing(
        text,
        "Portfolio Summary",
    )
    positions = _pages_containing(
        text,
        "Account Positions",
    )
    activity = _pages_containing(
        text,
        "Account Activity",
    )
    pending = _pages_containing(
        text,
        "Trades Pending Settlement",
    )

    if not summary:
        msg = "TD Ameritrade Portfolio Summary section not found."
        raise ValueError(msg)

    if not positions:
        msg = "TD Ameritrade Account Positions section not found."
        raise ValueError(msg)

    if not activity:
        msg = "TD Ameritrade Account Activity section not found."
        raise ValueError(msg)

    return StatementSections(
        summary=summary,
        positions=positions,
        activity=activity,
        pending=pending,
    )


def _pages_containing(
    text: StatementText,
    marker: str,
) -> tuple[StatementPage, ...]:
    """Return pages containing a structural marker."""
    return tuple(page for page in text.pages if marker in page.text)
