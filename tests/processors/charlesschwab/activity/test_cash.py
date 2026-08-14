"""
tests/processors/charlesschwab/activity/test_cash.py

Tests for Charles Schwab cash-transfer parsing.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from brokerage_statements.domain import (
    CashTransferEvent,
    CashTransferType,
    IncomeEvent,
    SourceEvidence,
)
from brokerage_statements.exceptions import UnknownActivityError
from brokerage_statements.processors.charlesschwab.activity.cash import (
    parse_cash_transfer,
)
from brokerage_statements.processors.charlesschwab.activity.rows import (
    ActivityRow,
)

from ._helpers import make_source, parse_rows


def test_parse_activity_preserves_tda_cash_migration() -> None:
    """TD migration cash should become an incoming cash transfer."""
    events = parse_rows(
        "Transaction Details\n"
        "11/06 Deposit AccountTransfer "
        "TDA TO CS&CO TRANSFER 414.71\n"
        "TotalTransactions $414.71"
    )

    assert len(events) == 1

    event = events[0]

    assert isinstance(event, CashTransferEvent)
    assert event.date == date(2023, 11, 6)
    assert event.transfer_type is CashTransferType.DEPOSIT
    assert event.amount == Decimal("414.71")


def test_parse_activity_rejects_malformed_deposit() -> None:
    """Recognized Schwab deposits should require amount data."""
    with pytest.raises(
        UnknownActivityError,
        match="Unable to parse Charles Schwab deposit row",
    ):
        parse_rows(
            "Transaction Details\n"
            "11/06 Deposit AccountTransfer BROKEN\n"
            "TotalTransactions $0.00"
        )


def test_parse_activity_rejects_unknown_deposit_semantics() -> None:
    """Unknown Schwab deposit descriptions must not be guessed."""
    with pytest.raises(
        UnknownActivityError,
        match="Unknown Charles Schwab account activity",
    ):
        parse_rows(
            "Transaction Details\n"
            "11/06 Deposit AccountTransfer UNKNOWN 10.00\n"
            "TotalTransactions $10.00"
        )


def test_cash_parser_ignores_non_deposit_activity() -> None:
    """Cash parser should decline unrelated activity categories."""
    events = parse_rows(
        "Transaction Details\n"
        "11/29 Interest CreditInterest "
        "SCHWAB1INT10/30-11/28 0.23\n"
        "TotalTransactions $0.23"
    )

    assert len(events) == 1
    assert isinstance(events[0], IncomeEvent)


def test_parse_cash_transfer_ignores_non_deposit_row() -> None:
    """Cash parser should decline unrelated activity categories."""
    row = ActivityRow(
        page_number=4,
        sequence=1,
        date="11/29",
        category="Interest",
        text="11/29 Interest CreditInterest TEST 0.23",
    )
    evidence = SourceEvidence(
        source=make_source(),
        page=4,
        section="Transaction Details",
        raw_text=row.text,
        processor="charlesschwab.monthly_2023",
        sequence=1,
    )

    assert (
        parse_cash_transfer(
            row,
            evidence,
            year=2023,
        )
        is None
    )


def test_parse_activity_preserves_compact_tda_cash_migration() -> None:
    """Compact PDF extraction should preserve TD migration cash."""
    events = parse_rows(
        "Transaction Details\n"
        "11/06 Deposit AccountTransfer "
        "TDATOCS&COTRANSFER 414.71\n"
        "TotalTransactions $414.71"
    )

    assert len(events) == 1

    event = events[0]

    assert isinstance(event, CashTransferEvent)
    assert event.transfer_type is CashTransferType.DEPOSIT
    assert event.amount == Decimal("414.71")
