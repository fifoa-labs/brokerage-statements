"""
tests/processors/tdameritrade/activity/test_corporate_actions.py

Tests for TD Ameritrade corporate-action activity parsing.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from brokerage_statements.domain import (
    CorporateActionEvent,
    CorporateActionType,
    FeeEvent,
)
from brokerage_statements.exceptions import UnknownActivityError

from ._helpers import parse_page, symbol_of


def test_parse_activity_consumes_reverse_split_delivery() -> None:
    """Old shares delivered for a reverse split should not be external."""
    events = parse_page(
        "Account Activity\n"
        "06/11/20 06/11/20 Cash Delivered - Other "
        "XPRESSPA GROUP INC 98420U604 500- 0.00 - 0.00\n"
        "1:3 R/S 6/11/20 98420U703\n"
        "1:3 REVERSE SPLIT TO XPRESSPA GROUP INC 98420U703\n"
        "Auto Reorg#480609|REVERSE SPLIT"
    )

    assert events == ()


def test_parse_activity_consumes_reverse_split_receipt() -> None:
    """New shares received from a reverse split should not be external."""
    events = parse_page(
        "Account Activity\n"
        "06/11/20 06/11/20 Cash Received - Other "
        "XPRESSPA GROUP INC XSPA 166 0.00 - 0.00\n"
        "COM\n"
        "1:3 REVERSE SPLIT TO XPRESSPA GROUP INC 98420U703\n"
        "Auto Reorg#480609|REVERSE SPLIT"
    )

    assert events == ()


def test_parse_activity_preserves_reorganization_fee() -> None:
    """Mandatory reorganization fees should remain explicit."""
    events = parse_page(
        "Account Activity\n"
        "06/11/20 06/11/20 Cash Journal - Expense "
        "MANDATORY REORGANIZATION 98420U604 - "
        "0.00 (38.00) (38.00)\n"
        "FEE\n"
        "Auto Reorg#480609"
    )

    assert len(events) == 1

    event = events[0]

    assert isinstance(event, FeeEvent)
    assert event.date == date(2020, 6, 11)
    assert event.amount == Decimal("38.00")
    assert event.description == "Mandatory Reorganization Fee"


def test_parse_activity_preserves_cash_in_lieu() -> None:
    """Fractional reverse-split proceeds should be corporate action cash."""
    events = parse_page(
        "Account Activity\n"
        "06/15/20 06/15/20 Cash Div/Int - Securities Sold "
        "XPRESSPA GROUP INC 98420U703 - 0.00 3.41 3.41\n"
        "1:3 R/S 6/11/20 98420U703\n"
        "REORGANIZATION\n"
        "CASH IN LIEU $5.12/SHARE\n"
        "Auto Reorg#480609\n"
        "Payable: 06/11/2020"
    )

    assert len(events) == 1

    event = events[0]

    assert isinstance(event, CorporateActionEvent)
    assert event.date == date(2020, 6, 15)
    assert event.action_type is CorporateActionType.CASH_IN_LIEU
    assert symbol_of(event.source_security) == "XSPA"
    assert event.target_security is None
    assert event.cash == Decimal("3.41")


def test_parse_activity_rejects_non_cash_in_lieu_security_sale() -> None:
    """Securities-sold income rows require explicit cash-in-lieu evidence."""
    row = (
        "06/15/20 06/15/20 Cash Div/Int - Securities Sold "
        "XPRESSPA GROUP INC 98420U703 - 0.00 3.41 3.41 "
        "REORGANIZATION OTHER PAYMENT"
    )

    with pytest.raises(
        UnknownActivityError,
        match="Unknown TD Ameritrade account activity",
    ):
        parse_page(
            f"Account Activity\n{row}",
        )
