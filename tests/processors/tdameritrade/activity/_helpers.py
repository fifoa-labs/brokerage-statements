"""
tests/processors/tdameritrade/activity/_helpers.py

Shared test helpers for TD Ameritrade account-activity parsing.
"""

from __future__ import annotations

from pathlib import Path

from brokerage_statements.domain import (
    Security,
    StatementSource,
    SymbolSecurity,
)
from brokerage_statements.processors.tdameritrade.activity import (
    ActivityEvent,
    parse_activity,
)
from brokerage_statements.processors.tdameritrade.sections import (
    StatementSections,
)
from brokerage_statements.text import StatementPage

PROCESSOR_NAME = "tdameritrade.monthly_2020"


def symbol_of(security: Security) -> str:
    """Return the symbol for a symbol-backed security."""
    assert isinstance(security, SymbolSecurity)
    return security.symbol


def make_source() -> StatementSource:
    """Return reusable statement source identity."""
    return StatementSource(
        path=Path("statement.pdf"),
        sha256="abc123",
    )


def make_sections(
    *pages: StatementPage,
) -> StatementSections:
    """Return statement sections containing account-activity pages."""
    return StatementSections(
        summary=(
            StatementPage(
                number=3,
                text="Portfolio Summary",
            ),
        ),
        positions=(
            StatementPage(
                number=4,
                text="Account Positions",
            ),
        ),
        activity=pages,
        pending=(),
    )


def parse_page(
    text: str,
    *,
    page_number: int = 5,
) -> tuple[ActivityEvent, ...]:
    """Parse one synthetic account-activity page."""
    return parse_activity(
        make_source(),
        make_sections(
            StatementPage(
                number=page_number,
                text=text,
            )
        ),
        processor_name=PROCESSOR_NAME,
    )
