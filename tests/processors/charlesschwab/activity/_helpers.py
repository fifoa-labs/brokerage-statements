"""
tests/processors/charlesschwab/activity/_helpers.py

Shared helpers for Charles Schwab account-activity tests.
"""

from __future__ import annotations

from pathlib import Path

from brokerage_statements.domain import StatementSource
from brokerage_statements.processors.charlesschwab.activity import (
    ActivityEvent,
    parse_activity,
)
from brokerage_statements.processors.charlesschwab.sections import (
    StatementSections,
)
from brokerage_statements.text import StatementPage

PROCESSOR_NAME = "charlesschwab.monthly_2023"


def make_source() -> StatementSource:
    """Return reusable statement source identity."""
    return StatementSource(
        path=Path("statement.pdf"),
        sha256="abc123",
    )


def make_sections(
    page: StatementPage,
) -> StatementSections:
    """Return sections containing one transaction-detail page."""
    summary = StatementPage(
        number=1,
        text="Account Summary",
    )
    positions = StatementPage(
        number=2,
        text="Positions - Summary",
    )
    transaction_summary = StatementPage(
        number=3,
        text="Transactions - Summary",
    )

    return StatementSections(
        summary=(summary,),
        positions=(positions,),
        transaction_summary=(transaction_summary,),
        transaction_details=(page,),
    )


def parse_rows(
    text: str,
    *,
    year: int = 2023,
) -> tuple[ActivityEvent, ...]:
    """Parse one synthetic Schwab transaction-detail page."""
    page = StatementPage(
        number=4,
        text=text,
    )

    return parse_activity(
        make_source(),
        make_sections(page),
        processor_name=PROCESSOR_NAME,
        year=year,
    )
