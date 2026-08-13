"""
tests/processors/tdameritrade/test_transition_2023.py

Tests for TD Ameritrade transition statement processing.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

from brokerage_statements.domain import (
    Broker,
    CashTransferEvent,
    StatementSource,
)
from brokerage_statements.processors.tdameritrade.transition_2023 import (
    Transition2023Processor,
)
from brokerage_statements.text import (
    StatementPage,
    StatementText,
)


def make_source() -> StatementSource:
    """Return reusable statement source identity."""
    return StatementSource(
        path=Path("statement.pdf"),
        sha256="abc123",
    )


def make_transition_text(
    *,
    activity: str = (
        "12/01/23 12/01/23 Cash Journal - Funds Disbursed "
        "TDA TO CS&CO TRANSFER - - 0.00 (0.02) 0.00"
    ),
) -> StatementText:
    """Return representative TD-to-Schwab transition statement text."""
    return StatementText(
        pages=(
            StatementPage(
                number=1,
                text=(
                    "Statement Reporting Period:\n"
                    "12/01/23 - 12/31/23\n"
                    "Statement for Account # 498-119578\n"
                    "Portfolio Summary\n"
                    "Total $ 0.00\n"
                    "Cash Activity Summary\n"
                    "Closing Balance $ 0.00"
                ),
            ),
            StatementPage(
                number=2,
                text=(
                    "Statement for Account # 498-119578\n"
                    "12/01/23 - 12/31/23\n"
                    "Account Activity\n"
                    "Opening Balance $0.02\n"
                    f"{activity}\n"
                    "Closing Balance $ 0.00\n"
                    "IDA FEATURE DURING TRANSITION\n"
                    "If your TD Ameritrade account was recently transitioned "
                    "to a Charles Schwab & Co., Inc. account."
                ),
            ),
        ),
    )


def test_transition_2023_properties() -> None:
    """Transition processor should expose stable identity."""
    processor = Transition2023Processor()

    assert processor.name == "tdameritrade.transition_2023"
    assert processor.broker is Broker.TD_AMERITRADE


def test_transition_2023_matches_transition_statement() -> None:
    """Transition markers should select the transition processor."""
    result = Transition2023Processor().match(
        make_transition_text(),
    )

    assert result.matched is True
    assert result.confidence == 100
    assert "transition" in result.reason.lower()


def test_transition_2023_rejects_normal_monthly_statement() -> None:
    """Normal TD monthly statements should not match transition grammar."""
    text = StatementText(
        pages=(
            StatementPage(
                number=1,
                text=(
                    "Statement Reporting Period:\n"
                    "10/01/23 - 10/31/23\n"
                    "Statement for Account # 498-119578\n"
                    "Portfolio Summary\n"
                    "Account Positions\n"
                    "Account Activity"
                ),
            ),
        ),
    )

    result = Transition2023Processor().match(text)

    assert result.matched is False
    assert result.confidence == 0
    assert "Missing TD Ameritrade transition markers" in result.reason


def test_transition_2023_parses_without_positions() -> None:
    """Transition statements should intentionally normalize no positions."""
    statement = Transition2023Processor().parse(
        make_source(),
        make_transition_text(),
    )

    assert statement.source == make_source()
    assert statement.broker is Broker.TD_AMERITRADE
    assert statement.processor_name == "tdameritrade.transition_2023"
    assert statement.account_id == "498-119578"
    assert statement.currency == "USD"
    assert statement.period.start == date(2023, 12, 1)
    assert statement.period.end == date(2023, 12, 31)
    assert statement.positions == ()


def test_transition_2023_preserves_cash_transfer() -> None:
    """Residual Schwab migration cash should remain a withdrawal."""
    statement = Transition2023Processor().parse(
        make_source(),
        make_transition_text(),
    )

    assert len(statement.events) == 1

    event = statement.events[0]

    assert isinstance(event, CashTransferEvent)
    assert event.amount == Decimal("0.02")
    assert event.evidence[0].processor == "tdameritrade.transition_2023"
