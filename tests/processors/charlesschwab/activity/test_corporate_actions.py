"""
tests/processors/charlesschwab/activity/test_corporate_actions.py

Tests for Charles Schwab corporate-action parsing.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from brokerage_statements.domain import (
    CorporateActionEvent,
    CorporateActionType,
    IncomeEvent,
    SourceEvidence,
    SymbolSecurity,
)
from brokerage_statements.exceptions import UnknownActivityError
from brokerage_statements.processors.charlesschwab.activity.corporate_actions import (  # noqa: E501
    parse_corporate_action,
)
from brokerage_statements.processors.charlesschwab.activity.rows import (
    ActivityRow,
)

from ._helpers import make_source, parse_rows


def make_evidence(
    *rows: ActivityRow,
) -> tuple[SourceEvidence, ...]:
    """Return evidence matching supplied activity rows."""
    return tuple(
        SourceEvidence(
            source=make_source(),
            page=row.page_number,
            section="Transaction Details",
            raw_text=row.text,
            processor="charlesschwab.monthly_2023",
            sequence=row.sequence,
        )
        for row in rows
    )


def test_parse_corporate_action_ignores_empty_rows() -> None:
    """Corporate-action parser should decline an empty row set."""
    assert (
        parse_corporate_action(
            (),
            (),
            year=2024,
        )
        is None
    )


def test_parse_corporate_action_ignores_non_other_activity() -> None:
    """Corporate-action parser should decline unrelated categories."""
    row = ActivityRow(
        page_number=4,
        sequence=1,
        date="02/09",
        category="Interest",
        text="02/09 Interest CreditInterest TEST 0.29",
    )

    assert (
        parse_corporate_action(
            (row,),
            make_evidence(row),
            year=2024,
        )
        is None
    )


def test_parse_corporate_action_ignores_non_reverse_split() -> None:
    """Other Activity rows need reverse-split grammar."""
    row = ActivityRow(
        page_number=4,
        sequence=1,
        date="02/09",
        category="Other Activity",
        text="02/09 Other Activity AccountTransfer TEST 1.0000",
    )

    assert (
        parse_corporate_action(
            (row,),
            make_evidence(row),
            year=2024,
        )
        is None
    )


def test_parse_activity_rejects_reverse_split_wrong_paired_category() -> None:
    """Reverse-split paired row must remain Other Activity."""
    first = ActivityRow(
        page_number=4,
        sequence=1,
        date="02/09",
        category="Other Activity",
        text=(
            "02/09 Other Activity ReverseSplit UAVS "
            "AGEAGLEAERIALSYSTEMSI 5.0000"
        ),
    )
    second = ActivityRow(
        page_number=4,
        sequence=2,
        date="02/09",
        category="Interest",
        text="02/09 Interest BROKEN",
    )

    with pytest.raises(
        UnknownActivityError,
        match="reverse split has unexpected paired row",
    ):
        parse_corporate_action(
            (first, second),
            make_evidence(first, second),
            year=2024,
        )


def test_parse_activity_preserves_reverse_split() -> None:
    """Paired reverse-split rows should become one corporate action."""
    events = parse_rows(
        "Transaction Details\n"
        "02/09 Other ReverseSplit UAVS "
        "AGEAGLEAERIALSYSTEMSI 5.0000\n"
        "Activity\n"
        "Other ReverseSplit "
        "AGEAGLEAERIALSYSTEMXXX (100.0000)\n"
        "Activity REVERSESPLIT\n"
        "TotalTransactions $0.00",
        year=2024,
    )

    assert len(events) == 1

    event = events[0]

    assert isinstance(event, CorporateActionEvent)
    assert event.date == date(2024, 2, 9)
    assert event.action_type is CorporateActionType.REVERSE_SPLIT
    assert event.source_security == SymbolSecurity("UAVS")
    assert event.target_security is None
    assert event.quantity_before == Decimal("100.0000")
    assert event.quantity_after == Decimal("5.0000")

    assert len(event.evidence) == 2
    assert event.evidence[0].sequence == 1
    assert event.evidence[1].sequence == 2


def test_parse_activity_rejects_unpaired_reverse_split() -> None:
    """Reverse splits should require both Schwab mechanical rows."""
    with pytest.raises(
        UnknownActivityError,
        match="reverse split is missing its paired row",
    ):
        parse_rows(
            "Transaction Details\n"
            "02/09 Other ReverseSplit UAVS "
            "AGEAGLEAERIALSYSTEMSI 5.0000\n"
            "Activity\n"
            "TotalTransactions $0.00",
            year=2024,
        )


def test_parse_activity_rejects_reverse_split_date_mismatch() -> None:
    """Paired reverse-split rows must represent the same action date."""
    with pytest.raises(
        UnknownActivityError,
        match="reverse split rows have different dates",
    ):
        parse_rows(
            "Transaction Details\n"
            "02/09 Other ReverseSplit UAVS "
            "AGEAGLEAERIALSYSTEMSI 5.0000\n"
            "Activity\n"
            "02/10 Other ReverseSplit "
            "AGEAGLEAERIALSYSTEMXXX (100.0000)\n"
            "Activity REVERSESPLIT\n"
            "TotalTransactions $0.00",
            year=2024,
        )


def test_parse_activity_rejects_malformed_reverse_split_pair() -> None:
    """Recognized reverse splits should require supported row grammar."""
    with pytest.raises(
        UnknownActivityError,
        match="Unable to parse Charles Schwab reverse split rows",
    ):
        parse_rows(
            "Transaction Details\n"
            "02/09 Other ReverseSplit UAVS "
            "AGEAGLEAERIALSYSTEMSI 5.0000\n"
            "Activity\n"
            "Other ReverseSplit BROKEN REMOVAL\n"
            "Activity\n"
            "TotalTransactions $0.00",
            year=2024,
        )


def test_parse_activity_preserves_reverse_split_and_interest_order() -> None:
    """Grouped corporate actions should preserve surrounding event order."""
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
