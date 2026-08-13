"""
tests/processors/tdameritrade/activity/test_trades.py

Tests for TD Ameritrade settled trade parsing.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from brokerage_statements.domain import (
    FeeEvent,
    TradeEvent,
    TradeSide,
    TradeStatus,
)
from brokerage_statements.exceptions import (
    UnknownActivityError,
    UnresolvedSecurityError,
)

from ._helpers import parse_page, symbol_of


def test_parse_activity_preserves_settled_buy() -> None:
    """Settled purchases should normalize into buy trades."""
    events = parse_page(
        "Account Activity\n"
        "03/19/20 03/20/20 Cash Buy - Securities Purchased "
        "DIREXION SHARES ETF TRUST NUGT "
        "200 5.52 (1,104.00) (104.00)"
    )

    assert len(events) == 1

    event = events[0]

    assert isinstance(event, TradeEvent)
    assert event.date == date(2020, 3, 19)
    assert event.settlement_date == date(2020, 3, 20)
    assert symbol_of(event.security) == "NUGT"
    assert event.side is TradeSide.BUY
    assert event.status is TradeStatus.SETTLED
    assert event.quantity == Decimal("200")
    assert event.price == Decimal("5.52")
    assert event.amount == Decimal("1104.00")
    assert event.position_effect is None


def test_parse_activity_preserves_settled_sell() -> None:
    """Settled sales should normalize quantity as a magnitude."""
    events = parse_page(
        "Account Activity\n"
        "03/23/20 03/25/20 Cash Sell - Securities Sold "
        "DIREXION SHARES ETF TRUST JNUG "
        "1,000- 4.14 4,139.79 3,320.79"
    )

    assert len(events) == 1

    event = events[0]

    assert isinstance(event, TradeEvent)
    assert symbol_of(event.security) == "JNUG"
    assert event.side is TradeSide.SELL
    assert event.status is TradeStatus.SETTLED
    assert event.quantity == Decimal("1000")
    assert event.price == Decimal("4.14")
    assert event.amount == Decimal("4139.79")
    assert event.date == date(2020, 3, 23)
    assert event.settlement_date == date(2020, 3, 25)


def test_parse_activity_emits_regulatory_fee_with_sale() -> None:
    """Regulatory fees should remain separate normalized events."""
    events = parse_page(
        "Account Activity\n"
        "03/23/20 03/25/20 Cash Sell - Securities Sold "
        "DIREXION SHARES ETF TRUST JNUG "
        "1,000- 4.14 4,139.79 3,320.79\n"
        "Regulatory Fee 0.21"
    )

    assert len(events) == 2

    trade = events[0]
    fee = events[1]

    assert isinstance(trade, TradeEvent)
    assert isinstance(fee, FeeEvent)

    assert symbol_of(trade.security) == "JNUG"
    assert fee.date == date(2020, 3, 25)
    assert fee.amount == Decimal("0.21")
    assert fee.description == "Regulatory Fee"
    assert trade.evidence == fee.evidence
    assert trade.evidence[0].sequence == 1


def test_parse_activity_joins_wrapped_trade_description() -> None:
    """Wrapped TD descriptions should form one logical activity row."""
    events = parse_page(
        "Account Activity\n"
        "03/24/20 03/26/20 Cash Buy - Securities Purchased "
        "BARCLAYS BANK PLC VXX 100 44.73 "
        "(4,473.00) (4,019.36)\n"
        "IPATH B SHRT TRM ETN"
    )

    assert len(events) == 1

    event = events[0]

    assert isinstance(event, TradeEvent)
    assert symbol_of(event.security) == "VXX"
    assert event.quantity == Decimal("100")
    assert event.price == Decimal("44.73")
    assert event.amount == Decimal("4473.00")

    raw_text = event.evidence[0].raw_text

    assert raw_text is not None
    assert "IPATH B SHRT TRM ETN" in raw_text


def test_parse_activity_resolves_uso_cusip() -> None:
    """USO reverse-split CUSIPs should resolve to the ticker."""
    events = parse_page(
        "Account Activity\n"
        "04/02/20 04/06/20 Cash Sell - Securities Sold "
        "UNITED STATES OIL FUND LP 91232N108 "
        "1,000- 4.86 4,859.77 4,859.77\n"
        "1:8 R/S 4/29/20 91232N207\n"
        "Regulatory Fee 0.23"
    )

    assert len(events) == 2

    trade = events[0]
    fee = events[1]

    assert isinstance(trade, TradeEvent)
    assert isinstance(fee, FeeEvent)
    assert symbol_of(trade.security) == "USO"
    assert trade.side is TradeSide.SELL
    assert trade.quantity == Decimal("1000")
    assert trade.price == Decimal("4.86")
    assert trade.amount == Decimal("4859.77")
    assert fee.amount == Decimal("0.23")

    raw_text = trade.evidence[0].raw_text

    assert raw_text is not None
    assert "91232N108" in raw_text
    assert "1:8 R/S 4/29/20 91232N207" in raw_text


def test_parse_activity_resolves_uso_cusip_on_buy() -> None:
    """CUSIP resolution should work for purchases and sales."""
    events = parse_page(
        "Account Activity\n"
        "04/22/20 04/24/20 Cash Buy - Securities Purchased "
        "UNITED STATES OIL FUND LP 91232N108 "
        "1,500 2.89 (4,335.00) (4,335.00)\n"
        "1:8 R/S 4/29/20 91232N207"
    )

    assert len(events) == 1

    trade = events[0]

    assert isinstance(trade, TradeEvent)
    assert symbol_of(trade.security) == "USO"
    assert trade.side is TradeSide.BUY
    assert trade.quantity == Decimal("1500")
    assert trade.price == Decimal("2.89")
    assert trade.amount == Decimal("4335.00")


def test_parse_activity_resolves_jnug_cusip() -> None:
    """JNUG reverse-split CUSIPs should resolve to the ticker."""
    events = parse_page(
        "Account Activity\n"
        "04/06/20 04/08/20 Cash Sell - Securities Sold "
        "DIREXION SHARES ETF TRUST 25460E166 "
        "1,000- 5.10 5,099.77 5,099.77\n"
        "1:10 R/S 4/23/20 25460G831\n"
        "Regulatory Fee 0.23"
    )

    assert len(events) == 2

    trade = events[0]

    assert isinstance(trade, TradeEvent)
    assert symbol_of(trade.security) == "JNUG"
    assert trade.quantity == Decimal("1000")


def test_parse_activity_rejects_unknown_cusip() -> None:
    """Unknown security identifiers should fail explicitly."""
    row = (
        "04/02/20 04/06/20 Cash Sell - Securities Sold "
        "UNKNOWN SECURITY 12345A678 "
        "100- 10.00 1,000.00 1,000.00"
    )

    with pytest.raises(
        UnresolvedSecurityError,
        match="Unresolved security identifier",
    ):
        parse_page(f"Account Activity\n{row}")


def test_parse_activity_rejects_malformed_trade() -> None:
    """Recognized trade rows with invalid tails should fail loudly."""
    row = "03/19/20 03/20/20 Cash Buy - Securities Purchased BROKEN TRADE ROW"

    with pytest.raises(
        UnknownActivityError,
        match="Unable to parse TD Ameritrade trade row",
    ):
        parse_page(f"Account Activity\n{row}")
