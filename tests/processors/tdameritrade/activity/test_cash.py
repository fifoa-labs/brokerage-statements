"""
tests/processors/tdameritrade/activity/test_cash.py

Tests for TD Ameritrade cash movement parsing.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from brokerage_statements.domain import (
    CashTransferEvent,
    CashTransferType,
)
from brokerage_statements.exceptions import UnknownActivityError

from ._helpers import parse_page


def test_parse_activity_preserves_external_deposit() -> None:
    """External funds deposited should become cash transfers."""
    events = parse_page(
        "Account Activity\n"
        "03/16/20 03/17/20 Cash - Funds Deposited "
        "ELECTRONIC FUNDING - - $ 0.00 $ 2,000.00 2,000.00"
    )

    assert len(events) == 1

    event = events[0]

    assert isinstance(event, CashTransferEvent)
    assert event.date == date(2020, 3, 17)
    assert event.transfer_type is CashTransferType.DEPOSIT
    assert event.amount == Decimal("2000.00")
    assert event.evidence[0].sequence == 1


def test_parse_activity_preserves_margin_deposit() -> None:
    """External deposits may be reported under margin account type."""
    events = parse_page(
        "Account Activity\n"
        "03/16/20 03/17/20 Margin - Funds Deposited "
        "ACH IN - - 0.00 1,000.00 1,000.00"
    )

    assert len(events) == 1

    event = events[0]

    assert isinstance(event, CashTransferEvent)
    assert event.transfer_type is CashTransferType.DEPOSIT
    assert event.amount == Decimal("1000.00")


def test_parse_activity_preserves_cash_award() -> None:
    """Cash awards reported as deposited funds should remain deposits."""
    events = parse_page(
        "Account Activity\n"
        "03/30/20 03/30/20 Cash Journal - Funds Deposited "
        "Cash Award - - 0.00 100.00 100.00"
    )

    assert len(events) == 1

    event = events[0]

    assert isinstance(event, CashTransferEvent)
    assert event.transfer_type is CashTransferType.DEPOSIT
    assert event.amount == Decimal("100.00")


def test_parse_activity_preserves_funds_disbursed() -> None:
    """External funds disbursed should become withdrawals."""
    events = parse_page(
        "Account Activity\n"
        "11/06/23 11/06/23 Cash Journal - Funds Disbursed "
        "TDA TO CS&CO TRANSFER - - 0.00 (414.71) 0.00"
    )

    assert len(events) == 1

    event = events[0]

    assert isinstance(event, CashTransferEvent)
    assert event.date == date(2023, 11, 6)
    assert event.transfer_type is CashTransferType.WITHDRAWAL
    assert event.amount == Decimal("414.71")


@pytest.mark.parametrize(
    "row",
    [
        (
            "03/17/20 03/17/20 Cash Journal - Other "
            "MOVE CASH BALANCE TO MARGIN "
            "- - 0.00 (2,000.00) 0.00"
        ),
        (
            "03/23/20 03/23/20 Cash Journal - Other "
            "PURCHASE FDIC INSURED DEPOSIT ACCOUNT "
            "- - 0.00 (2,500.00) 0.00"
        ),
        (
            "03/20/20 03/20/20 Cash Journal - Other "
            "REDEMPTION FDIC INSURED DEPOSIT ACCOUNT "
            "- - 0.00 1,220.00 0.00"
        ),
        (
            "03/19/20 03/19/20 Cash Journal - Other "
            "TRANSFER FROM 498-119578-2 "
            "TO 498-119578-1 "
            "- - 0.00 1,000.00 1,000.00"
        ),
    ],
)
def test_parse_activity_ignores_known_internal_cash_journals(
    row: str,
) -> None:
    """Known internal cash movements should not create events."""
    events = parse_page(f"Account Activity\n{row}")

    assert events == ()


def test_parse_activity_rejects_unknown_internal_journal() -> None:
    """Unknown journal semantics should not be silently ignored."""
    row = (
        "03/20/20 03/20/20 Cash Journal - Other "
        "UNRECOGNIZED INTERNAL ACTION "
        "- - 0.00 10.00 10.00"
    )

    with pytest.raises(
        UnknownActivityError,
        match="Unknown TD Ameritrade account activity",
    ):
        parse_page(f"Account Activity\n{row}")


def test_parse_activity_rejects_malformed_cash_transfer() -> None:
    """Recognized cash transfers should require amount data."""
    row = "03/16/20 03/17/20 Cash - Funds Deposited BROKEN CASH TRANSFER"

    with pytest.raises(
        UnknownActivityError,
        match="Unable to parse TD Ameritrade cash transfer row",
    ):
        parse_page(f"Account Activity\n{row}")
