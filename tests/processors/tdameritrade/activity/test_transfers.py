"""
tests/processors/tdameritrade/activity/test_transfers.py

Tests for TD Ameritrade security-transfer parsing.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from brokerage_statements.domain import (
    SecurityTransferDirection,
    SecurityTransferEvent,
)
from brokerage_statements.exceptions import UnknownActivityError

from ._helpers import parse_page, symbol_of


def test_parse_activity_preserves_external_security_delivery() -> None:
    """Migration deliveries should become outgoing security transfers."""
    events = parse_page(
        "Account Activity\n"
        "11/06/23 11/06/23 Cash Delivered - Other "
        "PHARMACOM BIOVET INC PHMB 2,000,000- 0.00 - 414.71\n"
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


def test_parse_activity_preserves_external_security_receipt() -> None:
    """External receipts should become incoming security transfers."""
    events = parse_page(
        "Account Activity\n"
        "03/19/20 03/19/20 Cash Received - Other "
        "TEST SECURITY TEST 300 0.00 - 0.00\n"
        "EXTERNAL TRANSFER"
    )

    assert len(events) == 1

    event = events[0]

    assert isinstance(event, SecurityTransferEvent)
    assert symbol_of(event.security) == "TEST"
    assert event.direction is SecurityTransferDirection.IN
    assert event.quantity == Decimal("300")


def test_parse_activity_ignores_internal_security_receipt() -> None:
    """Transfers between TD subaccounts should not become external events."""
    events = parse_page(
        "Account Activity\n"
        "03/19/20 03/19/20 Cash Received - Other "
        "DIREXION SHARES ETF TRUST NUGT 300 0.00 - 0.00\n"
        "DLY GOLD INDX 3X ETF\n"
        "TRANSFER FROM 498-119578-2"
    )

    assert events == ()


def test_parse_activity_ignores_internal_security_delivery() -> None:
    """Security delivered to another TD subaccount is internal."""
    events = parse_page(
        "Account Activity\n"
        "03/19/20 03/19/20 Margin Delivered - Other "
        "DIREXION SHARES ETF TRUST NUGT 300- 0.00 - 1,000.00\n"
        "DLY GOLD INDX 3X ETF\n"
        "TRANSFER TO 498-119578-1"
    )

    assert events == ()


def test_parse_activity_rejects_malformed_security_transfer() -> None:
    """Recognized security transfers should require security data."""
    row = "11/06/23 11/06/23 Cash Delivered - Other BROKEN SECURITY TRANSFER"

    with pytest.raises(
        UnknownActivityError,
        match="Unable to parse TD Ameritrade security transfer row",
    ):
        parse_page(f"Account Activity\n{row}")
