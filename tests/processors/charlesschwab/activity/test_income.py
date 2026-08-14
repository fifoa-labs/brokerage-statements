"""
tests/processors/charlesschwab/activity/test_income.py

Tests for Charles Schwab income parsing.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from brokerage_statements.domain import (
    IncomeEvent,
    IncomeType,
    SourceEvidence,
)
from brokerage_statements.exceptions import UnknownActivityError
from brokerage_statements.processors.charlesschwab.activity.income import (
    parse_income,
)
from brokerage_statements.processors.charlesschwab.activity.rows import (
    ActivityRow,
)

from ._helpers import make_source, parse_rows


def make_evidence(
    row: ActivityRow,
) -> SourceEvidence:
    """Return evidence matching one activity row."""
    return SourceEvidence(
        source=make_source(),
        page=row.page_number,
        section="Transaction Details",
        raw_text=row.text,
        processor="charlesschwab.monthly_2023",
        sequence=row.sequence,
    )


def test_parse_activity_preserves_schwab_interest() -> None:
    """Schwab One interest should become normalized income."""
    events = parse_rows(
        "Transaction Details\n"
        "11/29 Interest CreditInterest "
        "SCHWAB1INT10/30-11/28 0.23\n"
        "TotalTransactions $0.23"
    )

    assert len(events) == 1

    event = events[0]

    assert isinstance(event, IncomeEvent)
    assert event.date == date(2023, 11, 29)
    assert event.income_type is IncomeType.INTEREST
    assert event.amount == Decimal("0.23")


def test_parse_income_supports_spaced_credit_interest() -> None:
    """Interest parser should support spaced Schwab action text."""
    row = ActivityRow(
        page_number=4,
        sequence=1,
        date="11/29",
        category="Interest",
        text="11/29 Interest Credit Interest TEST 0.23",
    )

    event = parse_income(
        row,
        make_evidence(row),
        year=2023,
    )

    assert isinstance(event, IncomeEvent)
    assert event.amount == Decimal("0.23")


def test_parse_income_ignores_non_interest_row() -> None:
    """Income parser should decline unrelated activity categories."""
    row = ActivityRow(
        page_number=4,
        sequence=1,
        date="11/06",
        category="Deposit",
        text="11/06 Deposit AccountTransfer TEST 10.00",
    )

    assert (
        parse_income(
            row,
            make_evidence(row),
            year=2023,
        )
        is None
    )


def test_parse_income_rejects_malformed_interest() -> None:
    """Recognized interest rows should require supported grammar."""
    row = ActivityRow(
        page_number=4,
        sequence=1,
        date="11/29",
        category="Interest",
        text="11/29 Interest BROKEN",
    )

    with pytest.raises(
        UnknownActivityError,
        match="Unable to parse Charles Schwab interest row",
    ):
        parse_income(
            row,
            make_evidence(row),
            year=2023,
        )
