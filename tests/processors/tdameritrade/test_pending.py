"""
tests/processors/tdameritrade/test_pending.py

Tests for TD Ameritrade pending-trade parsing.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

from brokerage_statements.domain import (
    Security,
    StatementSource,
    SymbolSecurity,
    TradeSide,
    TradeStatus,
)
from brokerage_statements.processors.tdameritrade.pending import (
    parse_pending_trades,
)
from brokerage_statements.processors.tdameritrade.sections import (
    StatementSections,
)
from brokerage_statements.text import StatementPage


def symbol_of(security: Security) -> str:
    """Return the symbol for a symbol-backed security."""
    assert isinstance(security, SymbolSecurity)
    return security.symbol


def make_source() -> StatementSource:
    """Return reusable statement source identity."""
    return StatementSource(
        path=Path("statement.pdf"),
        sha256="abc123",
    )


def make_sections(
    *pages: StatementPage,
) -> StatementSections:
    """Return statement sections containing pending-trade pages."""
    summary = StatementPage(
        number=1,
        text="Portfolio Summary",
    )
    positions = StatementPage(
        number=2,
        text="Account Positions",
    )
    activity = StatementPage(
        number=3,
        text="Account Activity",
    )

    return StatementSections(
        summary=(summary,),
        positions=(positions,),
        activity=(activity,),
        pending=pages,
    )


def test_parse_pending_trades_preserves_buy() -> None:
    """Pending buys should preserve normalized trade data."""
    page = StatementPage(
        number=9,
        text=(
            "Trades Pending Settlement\n"
            "BUY VONAGE HLDGS CORPORATION Cash VG "
            "1,000 $ 6.90 03/30/20 04/01/20 $ (6,900.00)"
        ),
    )

    events = parse_pending_trades(
        make_source(),
        make_sections(page),
        processor_name="tdameritrade.monthly_2020",
    )

    assert len(events) == 1

    event = events[0]

    assert event.date == date(2020, 3, 30)
    assert symbol_of(event.security) == "VG"
    assert event.side is TradeSide.BUY
    assert event.status is TradeStatus.PENDING
    assert event.quantity == Decimal("1000")
    assert event.price == Decimal("6.90")
    assert event.amount == Decimal("6900.00")
    assert event.settlement_date == date(2020, 4, 1)
    assert event.position_effect is None

    assert len(event.evidence) == 1

    evidence = event.evidence[0]

    assert evidence.source == make_source()
    assert evidence.page == 9
    assert evidence.section == "Trades Pending Settlement"
    assert evidence.processor == "tdameritrade.monthly_2020"
    assert evidence.sequence == 1
    assert evidence.raw_text == (
        "BUY VONAGE HLDGS CORPORATION Cash VG "
        "1,000 $ 6.90 03/30/20 04/01/20 $ (6,900.00)"
    )


def test_parse_pending_trades_preserves_sell() -> None:
    """Pending sells should preserve normalized trade data."""
    page = StatementPage(
        number=9,
        text=(
            "Trades Pending Settlement\n"
            "SELL PLUG POWER INC Cash PLUG "
            "1,000- 3.64 03/31/20 04/02/20 3,639.80"
        ),
    )

    events = parse_pending_trades(
        make_source(),
        make_sections(page),
        processor_name="tdameritrade.monthly_2020",
    )

    assert len(events) == 1

    event = events[0]

    assert event.date == date(2020, 3, 31)
    assert symbol_of(event.security) == "PLUG"
    assert event.side is TradeSide.SELL
    assert event.status is TradeStatus.PENDING
    assert event.quantity == Decimal("1000")
    assert event.price == Decimal("3.64")
    assert event.amount == Decimal("3639.80")
    assert event.settlement_date == date(2020, 4, 2)


def test_parse_pending_trades_preserves_multiple_rows() -> None:
    """Pending trades should retain statement order."""
    page = StatementPage(
        number=9,
        text="Trades Pending Settlement\nBUY VONAGE HLDGS CORPORATION Cash VG 1,000 $ 6.90 03/30/20 04/01/20 $ (6,900.00)\nBUY PLUG POWER INC Cash PLUG 1,000 3.61 03/30/20 04/01/20 (3,610.00)\nSELL PLUG POWER INC Cash PLUG 1,000- 3.64 03/31/20 04/02/20 3,639.80\nSELL VONAGE HLDGS CORPORATION Cash VG 1,000- 7.03 03/31/20 04/02/20 7,029.74\nBUY AYTU BIOSCIENCE INC Cash AYTU 1,000 1.49 03/31/20 04/02/20 (1,490.00)",  # noqa: E501
    )

    events = parse_pending_trades(
        make_source(),
        make_sections(page),
        processor_name="tdameritrade.monthly_2020",
    )

    assert len(events) == 5

    assert [symbol_of(event.security) for event in events] == [
        "VG",
        "PLUG",
        "PLUG",
        "VG",
        "AYTU",
    ]
    assert [event.side for event in events] == [
        TradeSide.BUY,
        TradeSide.BUY,
        TradeSide.SELL,
        TradeSide.SELL,
        TradeSide.BUY,
    ]
    assert [event.evidence[0].sequence for event in events] == [
        1,
        2,
        3,
        4,
        5,
    ]


def test_parse_pending_trades_supports_margin_account() -> None:
    """Pending trades may originate from a margin account."""
    page = StatementPage(
        number=9,
        text=(
            "Trades Pending Settlement\n"
            "BUY TEST SECURITY Margin TEST "
            "25 10.50 03/30/20 04/01/20 (262.50)"
        ),
    )

    events = parse_pending_trades(
        make_source(),
        make_sections(page),
        processor_name="tdameritrade.monthly_2020",
    )

    assert len(events) == 1
    assert symbol_of(events[0].security) == "TEST"
    assert events[0].quantity == Decimal("25")


def test_parse_pending_trades_ignores_non_trade_lines() -> None:
    """Headers and unrelated lines should not become events."""
    page = StatementPage(
        number=9,
        text="Trades Pending Settlement\nAccount Symbol/ Trade Settle\nInvestment Description Type CUSIP Quantity Price Date Date Amount\nCOM\npage 7 of 9",  # noqa: E501
    )

    events = parse_pending_trades(
        make_source(),
        make_sections(page),
        processor_name="tdameritrade.monthly_2020",
    )

    assert events == ()


def test_parse_pending_trades_allows_missing_section() -> None:
    """Statements without pending trades should return no events."""
    events = parse_pending_trades(
        make_source(),
        make_sections(),
        processor_name="tdameritrade.monthly_2020",
    )

    assert events == ()
