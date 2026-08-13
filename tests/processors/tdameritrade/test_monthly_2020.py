"""
tests/processors/tdameritrade/test_monthly_2020.py

Tests for the TD Ameritrade monthly 2020 processor.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

from brokerage_statements.domain import (
    Broker,
    CashTransferEvent,
    Position,
    Security,
    StatementSource,
    SymbolSecurity,
    TradeEvent,
    TradeStatus,
)
from brokerage_statements.processors.tdameritrade import (
    BROKER_SIGNATURES,
    Monthly2020Processor,
)
from brokerage_statements.text import StatementPage, StatementText


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


def make_supported_text() -> StatementText:
    """Return representative TD Ameritrade monthly statement text."""
    return StatementText(
        pages=(
            StatementPage(
                number=1,
                text="\n".join(  # noqa: FLY002
                    (
                        "Statement Reporting Period:",
                        "03/01/20 - 03/31/20",
                        "Statement for Account # 498-119578",
                        "TD AMERITRADE",
                        "TD Ameritrade Clearing, Inc., Member SIPC",
                        "Portfolio Summary",
                    )
                ),
            ),
            StatementPage(
                number=2,
                text="\n".join(  # noqa: FLY002
                    (
                        "Account Positions",
                        (
                            "ASTC 1,000 2.60 2,600.00 03/27/20 "
                            "3,780.00 3.78 (1,180.00) - -"
                        ),
                    )
                ),
            ),
            StatementPage(
                number=3,
                text="\n".join(  # noqa: FLY002
                    (
                        "Account Activity",
                        (
                            "03/16/20 03/17/20 Cash - Funds Deposited "
                            "ELECTRONIC FUNDING - - "
                            "0.00 2,000.00 2,000.00"
                        ),
                        (
                            "03/19/20 03/20/20 Cash Buy - "
                            "Securities Purchased "
                            "DIREXION SHARES ETF TRUST NUGT "
                            "200 5.52 (1,104.00) (104.00)"
                        ),
                    )
                ),
            ),
            StatementPage(
                number=4,
                text="\n".join(  # noqa: FLY002
                    (
                        "Trades Pending Settlement",
                        (
                            "BUY VONAGE HLDGS CORPORATION Cash VG "
                            "1,000 6.90 03/30/20 04/01/20 "
                            "(6,900.00)"
                        ),
                    )
                ),
            ),
        ),
    )


def test_processor_identity() -> None:
    """Processor identity should remain stable."""
    processor = Monthly2020Processor()

    assert processor.name == "tdameritrade.monthly_2020"
    assert processor.broker is Broker.TD_AMERITRADE


def test_processor_matches_supported_statement() -> None:
    """Known monthly structure should match strongly."""
    match = Monthly2020Processor().match(
        make_supported_text(),
    )

    assert match.matched is True
    assert match.confidence == 100
    assert (
        match.reason == "Recognized TD Ameritrade monthly statement grammar."
    )


def test_processor_rejects_missing_structure() -> None:
    """Missing monthly markers should reject the processor."""
    match = Monthly2020Processor().match(
        StatementText(
            pages=(
                StatementPage(
                    number=1,
                    text="TD AMERITRADE",
                ),
            ),
        )
    )

    assert match.matched is False
    assert match.confidence == 0
    assert "Statement Reporting Period:" in match.reason


def test_processor_parses_normalized_statement() -> None:
    """Supported TD statements should normalize end-to-end."""
    statement = Monthly2020Processor().parse(
        make_source(),
        make_supported_text(),
    )

    assert statement.source == make_source()
    assert statement.broker is Broker.TD_AMERITRADE
    assert statement.processor_name == "tdameritrade.monthly_2020"
    assert statement.account_id == "498-119578"
    assert statement.currency == "USD"
    assert statement.period.start == date(2020, 3, 1)
    assert statement.period.end == date(2020, 3, 31)

    assert len(statement.positions) == 1

    position = statement.positions[0]

    assert isinstance(position, Position)
    assert symbol_of(position.security) == "ASTC"
    assert position.quantity == Decimal("1000")

    assert len(statement.events) == 3

    deposit = statement.events[0]
    settled_trade = statement.events[1]
    pending_trade = statement.events[2]

    assert isinstance(deposit, CashTransferEvent)
    assert deposit.amount == Decimal("2000.00")

    assert isinstance(settled_trade, TradeEvent)
    assert symbol_of(settled_trade.security) == "NUGT"
    assert settled_trade.status is TradeStatus.SETTLED

    assert isinstance(pending_trade, TradeEvent)
    assert symbol_of(pending_trade.security) == "VG"
    assert pending_trade.status is TradeStatus.PENDING
    assert pending_trade.settlement_date == date(2020, 4, 1)


def test_processor_allows_statement_without_pending_trades() -> None:
    """Pending trades should remain optional."""
    text = StatementText(
        pages=(
            StatementPage(
                number=1,
                text="\n".join(  # noqa: FLY002
                    (
                        "Statement Reporting Period:",
                        "09/01/21 - 09/30/21",
                        "Statement for Account # 498-119578",
                        "TD AMERITRADE",
                        "TD Ameritrade Clearing, Inc., Member SIPC",
                        "Portfolio Summary",
                    )
                ),
            ),
            StatementPage(
                number=2,
                text="\n".join(  # noqa: FLY002
                    (
                        "Account Positions",
                        (
                            "UAVS 1,500 3.01 4,515.00 02/11/21 "
                            "21,767.09 14.51 (17,252.09) - -"
                        ),
                    )
                ),
            ),
            StatementPage(
                number=3,
                text="\n".join(  # noqa: FLY002
                    (
                        "Account Activity",
                        (
                            "09/30/21 09/30/21 Cash Div/Int - Income "
                            "INTEREST CREDIT - - "
                            "0.00 0.02 2,887.83"
                        ),
                    )
                ),
            ),
        ),
    )

    statement = Monthly2020Processor().parse(
        make_source(),
        text,
    )

    assert len(statement.positions) == 1
    assert len(statement.events) == 1

    event = statement.events[0]

    assert symbol_of(statement.positions[0].security) == "UAVS"
    assert event.date == date(2021, 9, 30)


def test_td_broker_signature_is_stable() -> None:
    """TD package should expose its evidence-derived signature."""
    assert len(BROKER_SIGNATURES) == 1

    signature = BROKER_SIGNATURES[0]

    assert signature.name == "tdameritrade.monthly"
    assert signature.broker is Broker.TD_AMERITRADE
    assert signature.matches(
        make_supported_text(),
    )
