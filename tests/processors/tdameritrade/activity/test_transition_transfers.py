"""
tests/processors/tdameritrade/activity/test_transition_transfers.py

Tests for TD Ameritrade transition security transfers.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

from brokerage_statements.domain import (
    SecurityTransferDirection,
    SecurityTransferEvent,
    SourceEvidence,
    StatementSource,
)
from brokerage_statements.processors.tdameritrade.activity.transition_transfers import (  # noqa: E501
    parse_transition_security_transfer,
)

from ._helpers import parse_page, symbol_of


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
        processor="tdameritrade.transition_2023",
        sequence=1,
    )


def test_parse_activity_preserves_transition_security_transfer() -> None:
    """Transition deliveries should normalize as outgoing transfers."""
    events = parse_page(
        "Account Activity\n"
        "11/06/23 11/06/23 Cash Delivered - "
        "PHARMACOM BIOVET INC PHMB "
        "2,000,000- $ 0.00 $ - 414.71\n"
        "COM\n"
        "TDA TO CS&CO TRANSFER 4981195781"
    )

    assert len(events) == 1

    event = events[0]

    assert isinstance(event, SecurityTransferEvent)
    assert event.date == date(2023, 11, 6)
    assert symbol_of(event.security) == "PHMB"
    assert event.direction is SecurityTransferDirection.OUT
    assert event.quantity == Decimal("2000000")


def test_parse_transition_security_transfer_handles_uavs() -> None:
    """Transition parsing should derive identity from each row."""
    result = parse_transition_security_transfer(
        (
            "11/06/23 11/06/23 Cash Delivered - "
            "AGEAGLE AERIAL SYSTEMS INC UAVS "
            "100- 0.00 - 414.71 "
            "COM TDA TO CS&CO TRANSFER 4981195781"
        ),
        make_evidence(),
    )

    assert result is not None
    assert symbol_of(result.security) == "UAVS"
    assert result.quantity == Decimal("100")


def test_parse_transition_security_transfer_handles_warrant() -> None:
    """Transition deliveries should support symbol-backed warrants."""
    result = parse_transition_security_transfer(
        (
            "11/06/23 11/06/23 Cash Delivered - "
            "DIGITAL WORLD ACQUISITION CORP DWACW "
            "110- 0.00 - 414.71 "
            "WARRANT *CLBL EXP 06/30/2028 "
            "TDA TO CS&CO TRANSFER 4981195781"
        ),
        make_evidence(),
    )

    assert result is not None
    assert symbol_of(result.security) == "DWACW"
    assert result.quantity == Decimal("110")


def test_parse_transition_security_transfer_returns_none_for_unrelated_row() -> (  # noqa: E501
    None
):
    """Rows outside transition delivery grammar should not match."""
    result = parse_transition_security_transfer(
        (
            "11/06/23 11/06/23 Cash Journal - Funds Disbursed "
            "TDA TO CS&CO TRANSFER - - 0.00 (414.71) 0.00"
        ),
        make_evidence(),
    )

    assert result is None


def test_parse_transition_security_transfer_requires_transition_marker() -> (
    None
):
    """Delivered rows should require explicit Schwab transition evidence."""
    result = parse_transition_security_transfer(
        (
            "11/06/23 11/06/23 Cash Delivered - "
            "AGEAGLE AERIAL SYSTEMS INC UAVS "
            "100- 0.00 - 414.71 "
            "UNRELATED DELIVERY"
        ),
        make_evidence(),
    )

    assert result is None
