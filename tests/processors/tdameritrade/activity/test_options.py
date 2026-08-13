"""
tests/processors/tdameritrade/activity/test_options.py

Tests for TD Ameritrade option trade parsing.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from brokerage_statements.domain import (
    FeeEvent,
    OptionRight,
    OptionSecurity,
    PositionEffect,
    SourceEvidence,
    StatementSource,
    TradeEvent,
    TradeSide,
    TradeStatus,
)
from brokerage_statements.exceptions import UnknownActivityError
from brokerage_statements.processors.tdameritrade.activity.options import (
    parse_option_trade,
)

from ._helpers import parse_page


def option_security_of(event: TradeEvent) -> OptionSecurity:
    """Return the option security carried by a trade."""
    assert isinstance(event.security, OptionSecurity)
    return event.security


def test_parse_activity_preserves_option_buy_to_open() -> None:
    """Option purchases to open should preserve contract identity."""
    events = parse_page(
        "Account Activity\n"
        "07/15/20 07/16/20 Cash Buy - Securities Purchased "
        "SNAP INC - 2 2.19 (439.33) (439.33)\n"
        "SNAP Aug 21 20 25.0 C TO OPEN\n"
        "Commission/Fee 1.30\n"
        "Regulatory Fee 0.03"
    )

    assert len(events) == 3

    trade = events[0]
    commission = events[1]
    regulatory_fee = events[2]

    assert isinstance(trade, TradeEvent)
    assert isinstance(commission, FeeEvent)
    assert isinstance(regulatory_fee, FeeEvent)

    security = option_security_of(trade)

    assert security.underlying == "SNAP"
    assert security.expiration == date(2020, 8, 21)
    assert security.right is OptionRight.CALL
    assert security.strike == Decimal("25.0")

    assert trade.date == date(2020, 7, 15)
    assert trade.settlement_date == date(2020, 7, 16)
    assert trade.side is TradeSide.BUY
    assert trade.status is TradeStatus.SETTLED
    assert trade.position_effect is PositionEffect.OPEN
    assert trade.quantity == Decimal("2")
    assert trade.price == Decimal("2.19")
    assert trade.amount == Decimal("439.33")

    assert commission.amount == Decimal("1.30")
    assert commission.description == "Commission/Fee"

    assert regulatory_fee.amount == Decimal("0.03")
    assert regulatory_fee.description == "Regulatory Fee"

    assert trade.evidence == commission.evidence
    assert trade.evidence == regulatory_fee.evidence


def test_parse_activity_preserves_option_sell_to_close() -> None:
    """Option sales to close should preserve closing semantics."""
    events = parse_page(
        "Account Activity\n"
        "07/20/20 07/21/20 Cash Sell - Securities Sold "
        "SNAP INC - 2- 2.25 448.66 448.66\n"
        "SNAP Aug 21 20 25.0 C TO CLOSE\n"
        "Commission/Fee 1.30\n"
        "Regulatory Fee 0.04"
    )

    assert len(events) == 3

    trade = events[0]

    assert isinstance(trade, TradeEvent)

    security = option_security_of(trade)

    assert security.underlying == "SNAP"
    assert security.expiration == date(2020, 8, 21)
    assert security.right is OptionRight.CALL
    assert security.strike == Decimal("25.0")

    assert trade.side is TradeSide.SELL
    assert trade.position_effect is PositionEffect.CLOSE
    assert trade.quantity == Decimal("2")
    assert trade.price == Decimal("2.25")
    assert trade.amount == Decimal("448.66")


def test_parse_activity_preserves_second_option_underlying() -> None:
    """Option parsing should derive identity rather than hard-code SNAP."""
    events = parse_page(
        "Account Activity\n"
        "07/17/20 07/20/20 Cash Buy - Securities Purchased "
        "VODAFONE GROUP - 2 0.52 (105.33) 2,894.67\n"
        "VOD Aug 21 20 17.0 C TO OPEN\n"
        "Commission/Fee 1.30\n"
        "Regulatory Fee 0.03"
    )

    trade = events[0]

    assert isinstance(trade, TradeEvent)

    security = option_security_of(trade)

    assert security.underlying == "VOD"
    assert security.expiration == date(2020, 8, 21)
    assert security.strike == Decimal("17.0")


def test_parse_activity_preserves_option_close_with_small_premium() -> None:
    """Low-premium option closes should preserve exact decimals."""
    events = parse_page(
        "Account Activity\n"
        "07/27/20 07/28/20 Cash Sell - Securities Sold "
        "VODAFONE GROUP - 2- 0.09 16.67 16.67\n"
        "VOD Aug 21 20 17.0 C TO CLOSE\n"
        "Commission/Fee 1.30\n"
        "Regulatory Fee 0.03"
    )

    trade = events[0]

    assert isinstance(trade, TradeEvent)
    assert trade.price == Decimal("0.09")
    assert trade.amount == Decimal("16.67")
    assert trade.position_effect is PositionEffect.CLOSE


def test_parse_activity_preserves_put_option() -> None:
    """Put contracts should preserve their option right."""
    events = parse_page(
        "Account Activity\n"
        "07/15/20 07/16/20 Cash Buy - Securities Purchased "
        "SNAP INC - 1 1.50 (150.00) (150.00)\n"
        "SNAP Aug 21 20 20.0 P TO OPEN"
    )

    assert len(events) == 1

    trade = events[0]

    assert isinstance(trade, TradeEvent)

    security = option_security_of(trade)

    assert security.underlying == "SNAP"
    assert security.expiration == date(2020, 8, 21)
    assert security.right is OptionRight.PUT
    assert security.strike == Decimal("20.0")


def test_parse_activity_allows_option_without_commission_fee() -> None:
    """Option rows may omit a separate commission fee."""
    events = parse_page(
        "Account Activity\n"
        "07/15/20 07/16/20 Cash Buy - Securities Purchased "
        "SNAP INC - 1 1.50 (150.03) (150.03)\n"
        "SNAP Aug 21 20 20.0 C TO OPEN\n"
        "Regulatory Fee 0.03"
    )

    assert len(events) == 2

    trade = events[0]
    regulatory_fee = events[1]

    assert isinstance(trade, TradeEvent)
    assert isinstance(regulatory_fee, FeeEvent)

    assert regulatory_fee.description == "Regulatory Fee"
    assert regulatory_fee.amount == Decimal("0.03")


def test_parse_activity_allows_option_without_regulatory_fee() -> None:
    """Option rows may omit a separate regulatory fee."""
    events = parse_page(
        "Account Activity\n"
        "07/15/20 07/16/20 Cash Buy - Securities Purchased "
        "SNAP INC - 1 1.50 (151.30) (151.30)\n"
        "SNAP Aug 21 20 20.0 C TO OPEN\n"
        "Commission/Fee 1.30"
    )

    assert len(events) == 2

    trade = events[0]
    commission = events[1]

    assert isinstance(trade, TradeEvent)
    assert isinstance(commission, FeeEvent)

    assert commission.description == "Commission/Fee"
    assert commission.amount == Decimal("1.30")


def test_parse_activity_rejects_unsupported_option_month() -> None:
    """Unknown option month abbreviations should fail explicitly."""
    row = (
        "07/15/20 07/16/20 Cash Buy - Securities Purchased "
        "SNAP INC - 1 1.50 (150.00) (150.00)\n"
        "SNAP Xxx 21 20 20.0 C TO OPEN"
    )

    with pytest.raises(
        UnknownActivityError,
        match="Unsupported TD Ameritrade option month",
    ):
        parse_page(
            f"Account Activity\n{row}",
        )


def test_parse_option_trade_returns_none_without_option_identity() -> None:
    """Option-shaped rows without contract identity should not match."""
    source = StatementSource(
        path=Path("statement.pdf"),
        sha256="abc123",
    )
    evidence = SourceEvidence(
        source=source,
        page=5,
        section="Account Activity",
        raw_text="test row",
        processor="tdameritrade.monthly_2020",
        sequence=1,
    )

    result = parse_option_trade(
        (
            "07/15/20 07/16/20 Cash Buy - Securities Purchased "
            "SNAP INC - 2 2.19 (439.33) (439.33) "
            "NOT AN OPTION CONTRACT"
        ),
        evidence,
    )

    assert result is None
