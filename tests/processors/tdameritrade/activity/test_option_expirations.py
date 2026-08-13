"""
tests/processors/tdameritrade/activity/test_option_expirations.py

Tests for TD Ameritrade option expiration parsing.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from brokerage_statements.domain import (
    OptionExpirationEvent,
    OptionRight,
    OptionSecurity,
    SourceEvidence,
    StatementSource,
)
from brokerage_statements.exceptions import UnknownActivityError
from brokerage_statements.processors.tdameritrade.activity.option_expirations import (  # noqa: E501
    parse_option_expiration,
)

from ._helpers import parse_page


def make_evidence() -> SourceEvidence:
    """Return reusable source evidence."""
    source = StatementSource(
        path=Path("statement.pdf"),
        sha256="abc123",
    )

    return SourceEvidence(
        source=source,
        page=5,
        section="Account Activity",
        raw_text="test row",
        processor="tdameritrade.monthly_2020",
        sequence=1,
    )


def option_security_of(
    event: OptionExpirationEvent,
) -> OptionSecurity:
    """Return the option security carried by an expiration event."""
    assert isinstance(event.security, OptionSecurity)
    return event.security


def test_parse_activity_preserves_call_expiration() -> None:
    """Expired calls should preserve normalized contract identity."""
    events = parse_page(
        "Account Activity\n"
        "09/21/20 09/21/20 Cash Delivered - Other "
        "PROSHARES TRUST II - 20- 0.00 - 0.00\n"
        "UVXY Sep 18 20 30.0 C EXPIRATION"
    )

    assert len(events) == 1

    event = events[0]

    assert isinstance(event, OptionExpirationEvent)
    assert event.date == date(2020, 9, 21)
    assert event.contracts == Decimal("20")

    security = option_security_of(event)

    assert security.underlying == "UVXY"
    assert security.expiration == date(2020, 9, 18)
    assert security.right is OptionRight.CALL
    assert security.strike == Decimal("30.0")

    assert event.evidence[0].section == "Account Activity"
    assert event.evidence[0].sequence == 1


def test_parse_option_expiration_preserves_put() -> None:
    """Expired puts should preserve their option right."""
    result = parse_option_expiration(
        (
            "09/21/20 09/21/20 Cash Delivered - Other "
            "TEST SECURITY - 3- 0.00 - 0.00 "
            "TEST Sep 18 20 15.0 P EXPIRATION"
        ),
        make_evidence(),
    )

    assert result is not None

    security = option_security_of(result)

    assert security.underlying == "TEST"
    assert security.right is OptionRight.PUT
    assert security.strike == Decimal("15.0")
    assert result.contracts == Decimal("3")


def test_parse_option_expiration_returns_none_for_unrelated_row() -> None:
    """Rows outside the delivered-other grammar should not match."""
    result = parse_option_expiration(
        (
            "09/21/20 09/21/20 Cash Buy - Securities Purchased "
            "TEST SECURITY TEST 1 10.00 (10.00) (10.00)"
        ),
        make_evidence(),
    )

    assert result is None


def test_parse_option_expiration_returns_none_without_identity() -> None:
    """Delivered rows without expiration identity should not match."""
    result = parse_option_expiration(
        (
            "09/21/20 09/21/20 Cash Delivered - Other "
            "PROSHARES TRUST II - 20- 0.00 - 0.00 "
            "NOT AN OPTION EXPIRATION"
        ),
        make_evidence(),
    )

    assert result is None


def test_parse_option_expiration_rejects_unknown_month() -> None:
    """Unknown option month abbreviations should fail explicitly."""
    with pytest.raises(
        UnknownActivityError,
        match="Unsupported TD Ameritrade option month",
    ):
        parse_option_expiration(
            (
                "09/21/20 09/21/20 Cash Delivered - Other "
                "TEST SECURITY - 3- 0.00 - 0.00 "
                "TEST Xxx 18 20 15.0 C EXPIRATION"
            ),
            make_evidence(),
        )


def test_parse_activity_preserves_received_option_expiration() -> None:
    """Expired option positions may be reported as received."""
    events = parse_page(
        "Account Activity\n"
        "10/12/20 10/12/20 Cash Received - Other "
        "PROSHARES TRUST II - 13 0.00 - 0.00\n"
        "UVXY Oct 09 20 21.0 C EXPIRATION"
    )

    assert len(events) == 1

    event = events[0]

    assert isinstance(event, OptionExpirationEvent)
    assert event.date == date(2020, 10, 12)
    assert event.contracts == Decimal("13")

    security = option_security_of(event)

    assert security.underlying == "UVXY"
    assert security.expiration == date(2020, 10, 9)
    assert security.right is OptionRight.CALL
    assert security.strike == Decimal("21.0")
