"""
tests/processors/charlesschwab/test_monthly_2023.py

Tests for the Charles Schwab monthly 2023 processor.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from brokerage_statements.domain import (
    Broker,
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


def test_parse_reaches_activity_normalization_boundary() -> None:
    """Parsing should stop after proven logical activity-row extraction."""
    processor = Monthly2023Processor()

    with pytest.raises(
        NotImplementedError,
        match=(
            "Charles Schwab monthly activity normalization is not implemented"
        ),
    ):
        processor.parse(
            make_source(),
            make_supported_text(),
        )
