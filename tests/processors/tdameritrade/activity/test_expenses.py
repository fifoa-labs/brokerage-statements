"""
tests/processors/tdameritrade/activity/test_expenses.py

Tests for TD Ameritrade expense parsing.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

from brokerage_statements.domain import (
    FeeEvent,
    SourceEvidence,
    StatementSource,
)
from brokerage_statements.processors.tdameritrade.activity.expenses import (
    parse_expense,
)

from ._helpers import parse_page


def make_evidence() -> SourceEvidence:
    """Return reusable source evidence."""
    return SourceEvidence(
        source=StatementSource(
            path=Path("statement.pdf"),
            sha256="abc123",
        ),
        page=5,
        section="Account Activity",
        raw_text="test row",
        processor="tdameritrade.monthly_2020",
        sequence=1,
    )


def test_parse_activity_preserves_margin_interest_expense() -> None:
    """Margin interest charges should normalize as explicit fees."""
    events = parse_page(
        "Account Activity\n"
        "01/29/21 01/29/21 Margin Div/Int - Expense "
        "MARGIN INTEREST CHARGE - - 0.00 (4.57) (2,829.94)\n"
        "Payable: 01/29/2021"
    )

    assert len(events) == 1

    event = events[0]

    assert isinstance(event, FeeEvent)
    assert event.date == date(2021, 1, 29)
    assert event.amount == Decimal("4.57")
    assert event.description == "Margin Interest Charge"


def test_parse_expense_returns_none_for_unrelated_row() -> None:
    """Rows outside supported expense grammar should not match."""
    result = parse_expense(
        (
            "01/29/21 01/29/21 Margin Div/Int - Other "
            "UNRELATED ACTIVITY - - 0.00 1.00 1.00"
        ),
        make_evidence(),
    )

    assert result is None
