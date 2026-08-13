"""
tests/processors/charlesschwab/test_monthly_2023.py

Tests for the Charles Schwab monthly 2023 statement processor.
"""

from __future__ import annotations

import pytest

from brokerage_statements.domain import Broker
from brokerage_statements.processors.charlesschwab import (
    Monthly2023Processor,
)
from brokerage_statements.text import (
    StatementPage,
    StatementText,
)


def make_text(value: str) -> StatementText:
    """Return one-page statement text."""
    return StatementText(
        pages=(
            StatementPage(
                number=1,
                text=value,
            ),
        ),
    )


def test_processor_name_is_stable() -> None:
    """Processor should expose its stable identifier."""
    processor = Monthly2023Processor()

    assert processor.name == "charlesschwab.monthly_2023"


def test_processor_broker_is_charles_schwab() -> None:
    """Processor should declare Charles Schwab ownership."""
    processor = Monthly2023Processor()

    assert processor.broker is Broker.CHARLES_SCHWAB


def test_processor_matches_observed_monthly_grammar() -> None:
    """Observed Schwab monthly markers should match strongly."""
    processor = Monthly2023Processor()

    result = processor.match(
        make_text(
            "Schwab One® Account of\n"
            "Account Summary\n"
            "Positions - Summary\n"
            "Transaction Details"
        )
    )

    assert result.matched
    assert result.confidence == 100
    assert result.reason == (
        "Recognized Charles Schwab monthly statement grammar."
    )


def test_processor_rejects_missing_monthly_marker() -> None:
    """Missing required structure should reject the statement."""
    processor = Monthly2023Processor()

    result = processor.match(
        make_text(
            "Schwab One® Account of\nAccount Summary\nTransaction Details"
        )
    )

    assert not result.matched
    assert result.confidence == 0
    assert result.reason == (
        "Missing Charles Schwab monthly markers: Positions - Summary"
    )


def test_processor_rejects_unrelated_statement() -> None:
    """Unrelated statement text should not match Schwab grammar."""
    processor = Monthly2023Processor()

    result = processor.match(
        make_text("Completely unrelated brokerage statement")
    )

    assert not result.matched
    assert result.confidence == 0
    assert result.reason == (
        "Missing Charles Schwab monthly markers: "
        "Schwab One® Account of, "
        "Account Summary, "
        "Positions - Summary, "
        "Transaction Details"
    )


def test_parse_is_not_implemented_yet() -> None:
    """Processor parsing should remain explicit until implemented."""
    processor = Monthly2023Processor()
    text = make_text(
        "Schwab One® Account of\n"
        "Account Summary\n"
        "Positions - Summary\n"
        "Transaction Details"
    )

    with pytest.raises(NotImplementedError):
        processor.parse(
            source=None,  # type: ignore[arg-type]
            text=text,
        )
