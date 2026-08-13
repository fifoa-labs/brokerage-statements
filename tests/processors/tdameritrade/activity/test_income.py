"""
tests/processors/tdameritrade/activity/test_income.py

Tests for TD Ameritrade account-activity income parsing.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from brokerage_statements.domain import (
    IncomeEvent,
    IncomeType,
)
from brokerage_statements.exceptions import UnknownActivityError

from ._helpers import parse_page


def test_parse_activity_preserves_interest_income() -> None:
    """Interest credits should normalize as interest income."""
    events = parse_page(
        "Account Activity\n"
        "09/30/21 09/30/21 Cash Div/Int - Income "
        "INTEREST CREDIT Payable: 09/30/2021 "
        "- - 0.00 0.02 2,887.83"
    )

    assert len(events) == 1

    event = events[0]

    assert isinstance(event, IncomeEvent)
    assert event.date == date(2021, 9, 30)
    assert event.income_type is IncomeType.INTEREST
    assert event.amount == Decimal("0.02")


def test_parse_activity_rejects_malformed_income() -> None:
    """Recognized income rows should require amount data."""
    row = "09/30/21 09/30/21 Cash Div/Int - Income BROKEN INCOME"

    with pytest.raises(
        UnknownActivityError,
        match="Unable to parse TD Ameritrade income row",
    ):
        parse_page(f"Account Activity\n{row}")
