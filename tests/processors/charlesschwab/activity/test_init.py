"""
tests/processors/charlesschwab/activity/test_init.py

Tests for Charles Schwab account-activity orchestration.
"""

from __future__ import annotations

import pytest

from brokerage_statements.domain import (
    CashTransferEvent,
    CorporateActionEvent,
    IncomeEvent,
    SecurityTransferEvent,
)
from brokerage_statements.exceptions import UnknownActivityError
from brokerage_statements.processors.charlesschwab.activity import (
    _parse_grouped_corporate_action,
)

from ._helpers import PROCESSOR_NAME, make_source, parse_rows


def test_parse_activity_preserves_event_order() -> None:
    """Normalized events should preserve statement order."""
    events = parse_rows(
        "Transaction Details\n"
        "11/06 Deposit AccountTransfer "
        "TDA TO CS&CO TRANSFER 414.71\n"
        "Other AccountTransfer UAVS "
        "AGEAGLEAERIALSYSTEMSI 100.0000 0.1278 12.78\n"
        "Activity\n"
        "11/29 Interest CreditInterest "
        "SCHWAB1INT10/30-11/28 0.23\n"
        "TotalTransactions $427.72"
    )

    assert len(events) == 3
    assert isinstance(events[0], CashTransferEvent)
    assert isinstance(events[1], SecurityTransferEvent)
    assert isinstance(events[2], IncomeEvent)

    assert [event.evidence[0].sequence for event in events] == [
        1,
        2,
        3,
    ]


def test_parse_activity_preserves_grouped_corporate_action_order() -> None:
    """Grouped corporate actions should consume their paired rows once."""
    events = parse_rows(
        "Transaction Details\n"
        "02/09 Other ReverseSplit UAVS "
        "AGEAGLEAERIALSYSTEMSI 5.0000\n"
        "Activity\n"
        "Other ReverseSplit "
        "AGEAGLEAERIALSYSTEMXXX (100.0000)\n"
        "Activity REVERSESPLIT\n"
        "02/28 Interest CreditInterest "
        "SCHWAB1INT01/30-02/27 0.29\n"
        "TotalTransactions $0.29",
        year=2024,
    )

    assert len(events) == 2
    assert isinstance(events[0], CorporateActionEvent)
    assert isinstance(events[1], IncomeEvent)

    assert [
        evidence.sequence for event in events for evidence in event.evidence
    ] == [
        1,
        2,
        3,
    ]


def test_parse_activity_allows_no_transaction_details() -> None:
    """Statements without transaction details should produce no events."""
    events = parse_rows("")

    assert events == ()


def test_parse_activity_rejects_unknown_activity() -> None:
    """Unknown activity should fail rather than disappear."""
    with pytest.raises(
        UnknownActivityError,
        match="Unknown Charles Schwab account activity",
    ):
        parse_rows(
            "Transaction Details\n"
            "11/29 Fee MysteryAction UNSUPPORTED 10.00\n"
            "TotalTransactions $10.00"
        )


def test_grouped_corporate_action_ignores_empty_rows() -> None:
    """Grouped corporate-action parsing should decline empty input."""
    result = _parse_grouped_corporate_action(
        source=make_source(),
        rows=(),
        processor_name=PROCESSOR_NAME,
        year=2024,
    )

    assert result is None
