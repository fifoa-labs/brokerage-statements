"""
tests/processors/charlesschwab/test_monthly_2023.py

Tests for the Charles Schwab monthly 2023 processor.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from brokerage_statements.domain import (
    Broker,
    StatementPeriod,
    StatementSource,
)
from brokerage_statements.processors.charlesschwab import (
    Monthly2023Processor,
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


def make_supported_text() -> StatementText:
    """Return representative Charles Schwab monthly statement text."""
    return StatementText(
        pages=(
            StatementPage(
                number=1,
                text=(
                    "Schwab One® Account of\n"
                    "AccountNumber StatementPeriod\n"
                    "ACCOUNTOWNER 1234-5678 November1-30,2023\n"
                    "Account Summary"
                ),
            ),
            StatementPage(
                number=2,
                text="Positions - Summary",
            ),
            StatementPage(
                number=3,
                text=(
                    "Positions - Equities\n"
                    "TEST SAMPLE SECURITY "
                    "100.0000 1.00000 100.00 "
                    "90.00 10.00 N/A 0.00 10%\n"
                    "Total Equities $100.00\n"
                    "Transactions - Summary"
                ),
            ),
            StatementPage(
                number=4,
                text=(
                    "Transaction Details\n"
                    "11/29 Interest CreditInterest "
                    "SCHWAB1INT10/30-11/28 0.23\n"
                    "TotalTransactions $0.23\n"
                    "Terms and Conditions"
                ),
            ),
        ),
    )


def test_processor_identity() -> None:
    """Processor identity should remain stable."""
    processor = Monthly2023Processor()

    assert processor.name == "charlesschwab.monthly_2023"
    assert processor.broker is Broker.CHARLES_SCHWAB


def test_processor_matches_supported_statement() -> None:
    """Known Schwab monthly structure should match strongly."""
    match = Monthly2023Processor().match(
        make_supported_text(),
    )

    assert match.matched is True
    assert match.confidence == 100
    assert match.reason == (
        "Recognized Charles Schwab monthly statement grammar."
    )


def test_processor_allows_missing_transaction_details() -> None:
    """Statements without activity may omit transaction details."""
    match = Monthly2023Processor().match(
        make_supported_text(),
    )

    assert match.matched is True
    assert match.confidence == 100


def test_processor_rejects_missing_structure() -> None:
    """Missing monthly markers should reject the processor."""
    match = Monthly2023Processor().match(
        StatementText(
            pages=(
                StatementPage(
                    number=1,
                    text="Schwab One® Account of",
                ),
            ),
        )
    )

    assert match.matched is False
    assert match.confidence == 0
    assert "Account Summary" in match.reason
    assert "Positions - Summary" in match.reason
    assert "Transactions - Summary" in match.reason


def test_parse_returns_normalized_statement() -> None:
    """Supported Schwab text should produce a parsed statement."""
    statement = Monthly2023Processor().parse(
        make_source(),
        make_supported_text(),
    )

    assert statement.broker is Broker.CHARLES_SCHWAB
    assert statement.processor_name == "charlesschwab.monthly_2023"
    assert statement.account_id == "1234-5678"
    assert statement.period == StatementPeriod(
        start=date(2023, 11, 1),
        end=date(2023, 11, 30),
    )

    assert len(statement.positions) == 1
    assert len(statement.events) == 1
