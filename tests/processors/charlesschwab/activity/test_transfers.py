"""
tests/processors/charlesschwab/activity/test_transfers.py

Tests for Charles Schwab security-transfer parsing.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from brokerage_statements.domain import (
    SecurityTransferDirection,
    SecurityTransferEvent,
    SourceEvidence,
    SymbolSecurity,
)
from brokerage_statements.exceptions import UnknownActivityError
from brokerage_statements.processors.charlesschwab.activity import transfers
from brokerage_statements.processors.charlesschwab.activity.rows import (
    ActivityRow,
)
from brokerage_statements.processors.charlesschwab.activity.transfers import (
    parse_security_transfer,
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


def test_parse_activity_preserves_standard_security_transfer() -> None:
    """Standard Schwab transfer quantity should normalize exactly."""
    events = parse_rows(
        "Transaction Details\n"
        "11/06 Other AccountTransfer UAVS "
        "AGEAGLEAERIALSYSTEMSI 100.0000 0.1278 12.78\n"
        "Activity\n"
        "TotalTransactions $12.78"
    )

    assert len(events) == 1

    event = events[0]

    assert isinstance(event, SecurityTransferEvent)
    assert event.date == date(2023, 11, 6)
    assert event.security == SymbolSecurity("UAVS")
    assert event.direction is SecurityTransferDirection.IN
    assert event.quantity == Decimal("100.0000")


def test_parse_activity_preserves_wrapped_warrant_transfer() -> None:
    """Wrapped Schwab warrant rows should preserve transfer quantity."""
    events = parse_rows(
        "Transaction Details\n"
        "11/06 Other AccountTransfer DWACW "
        "DIGITALWORLDACQ28\n"
        "Activity WTFWARRANTSEXP 06/30/28\n"
        "110.0000 4.7600 523.60\n"
        "TotalTransactions $523.60"
    )

    assert len(events) == 1

    event = events[0]

    assert isinstance(event, SecurityTransferEvent)
    assert event.security == SymbolSecurity("DWACW")
    assert event.quantity == Decimal("110.0000")


def test_parse_activity_reconstructs_split_transfer_quantity() -> None:
    """Split Schwab quantity digits should be reconstructed."""
    events = parse_rows(
        "Transaction Details\n"
        "11/06 Other AccountTransfer PHMB "
        "PHARMACOMBIOVETINC 2,000,000.000\n"
        "Activity 0\n"
        "0.00\n"
        "TotalTransactions $0.00"
    )

    assert len(events) == 1

    event = events[0]

    assert isinstance(event, SecurityTransferEvent)
    assert event.security == SymbolSecurity("PHMB")
    assert event.quantity == Decimal("2000000.0000")


def test_parse_security_transfer_ignores_non_other_activity() -> None:
    """Transfer parser should decline unrelated activity categories."""
    row = ActivityRow(
        page_number=4,
        sequence=1,
        date="11/06",
        category="Deposit",
        text="11/06 Deposit AccountTransfer TEST 10.00",
    )

    assert (
        parse_security_transfer(
            row,
            make_evidence(row),
            year=2023,
        )
        is None
    )


def test_parse_security_transfer_ignores_non_account_transfer() -> None:
    """Other Activity rows need AccountTransfer grammar."""
    row = ActivityRow(
        page_number=4,
        sequence=1,
        date="11/06",
        category="Other Activity",
        text=("11/06 Other Activity MysteryAction TEST SECURITY 10.0000"),
    )

    assert (
        parse_security_transfer(
            row,
            make_evidence(row),
            year=2023,
        )
        is None
    )


def test_parse_security_transfer_rejects_missing_quantity() -> None:
    """Recognized transfer rows should require quantity data."""
    row = ActivityRow(
        page_number=4,
        sequence=1,
        date="11/06",
        category="Other Activity",
        text=(
            "11/06 Other Activity AccountTransfer TEST "
            "SECURITY WITHOUT QUANTITY"
        ),
    )

    with pytest.raises(
        UnknownActivityError,
        match="Unable to parse Charles Schwab security transfer row",
    ):
        parse_security_transfer(
            row,
            make_evidence(row),
            year=2023,
        )


def test_parse_activity_reconstructs_split_quantity_after_value() -> None:
    """Split quantity digit may follow another numeric column."""
    events = parse_rows(
        "Transaction Details\n"
        "11/06 Other AccountTransfer PHMB "
        "PHARMACOMBIOVETINC 2,000,000.000\n"
        "Activity 0.00\n"
        "0\n"
        "TotalTransactions $0.00"
    )

    assert len(events) == 1

    event = events[0]

    assert isinstance(event, SecurityTransferEvent)
    assert event.security == SymbolSecurity("PHMB")
    assert event.quantity == Decimal("2000000.0000")


def test_parse_security_transfer_skips_non_quantity_numeric_tokens() -> None:
    """Numeric values that are not quantity candidates should be ignored."""
    row = ActivityRow(
        page_number=4,
        sequence=1,
        date="11/06",
        category="Other Activity",
        text=(
            "11/06 Other Activity AccountTransfer TEST SECURITY 10.25 20.50"
        ),
    )

    with pytest.raises(
        UnknownActivityError,
        match="Unable to parse Charles Schwab security transfer row",
    ):
        parse_security_transfer(
            row,
            make_evidence(row),
            year=2023,
        )


def test_parse_security_transfer_rejects_unrecoverable_split_quantity() -> (
    None
):
    """Three-decimal quantities require a recoverable fourth digit."""
    row = ActivityRow(
        page_number=4,
        sequence=1,
        date="11/06",
        category="Other Activity",
        text=(
            "11/06 Other Activity AccountTransfer TEST SECURITY 100.000 25.50"
        ),
    )

    with pytest.raises(
        UnknownActivityError,
        match="Unable to parse Charles Schwab security transfer row",
    ):
        parse_security_transfer(
            row,
            make_evidence(row),
            year=2023,
        )


def test_reconstruct_split_quantity_skips_non_digit_tokens() -> None:
    """Split quantity reconstruction should ignore unrelated values."""
    quantity = transfers._reconstruct_split_quantity(  # noqa: SLF001
        "2,000,000.000",
        (
            "0.00",
            "0",
        ),
    )

    assert quantity == Decimal("2000000.0000")


def test_reconstruct_split_quantity_returns_none_without_tail_digit() -> None:
    """Split quantity reconstruction should fail without one digit."""
    quantity = transfers._reconstruct_split_quantity(  # noqa: SLF001
        "2,000,000.000",
        (
            "0.00",
            "12",
            "ABC",
        ),
    )

    assert quantity is None
