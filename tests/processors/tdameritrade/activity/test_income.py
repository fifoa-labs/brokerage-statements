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


def test_parse_activity_preserves_insured_deposit_interest() -> None:
    """FDIC insured deposit interest should normalize as interest income."""
    events = parse_page(
        "Account Activity\n"
        "01/15/21 01/15/21 Margin Div/Int - Other "
        "FDIC INSURED DEPOSIT MMDA1 - 0.00 0.11 0.11\n"
        "ACCOUNT\n"
        "CORE NOT COVERED BY SIPC\n"
        "Interest: Insured Deposit Account Bank NA\n"
        "Payable: 01/31/2021\n"
        "Insured Deposit Account Interest\n"
        "0.11"
    )

    assert len(events) == 1

    event = events[0]

    assert isinstance(event, IncomeEvent)
    assert event.date == date(2021, 1, 15)
    assert event.income_type is IncomeType.INTEREST
    assert event.amount == Decimal("0.11")


def test_parse_income_ignores_unrecognized_div_int_other() -> None:
    """Unrecognized Div/Int Other rows should not be guessed as income."""
    row = (
        "01/15/21 01/15/21 Margin Div/Int - Other "
        "UNRELATED ACTIVITY - 0.00 0.11 0.11"
    )

    with pytest.raises(
        UnknownActivityError,
        match="Unknown TD Ameritrade account activity",
    ):
        parse_page(
            f"Account Activity\n{row}",
        )


def test_parse_income_rejects_unmarked_insured_deposit_other() -> None:
    """Insured deposit rows require explicit interest evidence."""
    row = (
        "01/15/21 01/15/21 Margin Div/Int - Other "
        "FDIC INSURED DEPOSIT MMDA1 - 0.00 0.11 0.11 "
        "ACCOUNT CORE NOT COVERED BY SIPC "
        "UNRELATED ACTIVITY"
    )

    with pytest.raises(
        UnknownActivityError,
        match="Unknown TD Ameritrade account activity",
    ):
        parse_page(
            f"Account Activity\n{row}",
        )
