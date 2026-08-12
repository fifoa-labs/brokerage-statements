"""
tests/processors/test_base.py

Tests for statement processor matching contracts.
"""

from __future__ import annotations

import pytest

from brokerage_statements.processors import ProcessorMatch


def test_processor_match_preserves_values() -> None:
    """Valid processor matches should preserve their metadata."""
    match = ProcessorMatch(
        matched=True,
        confidence=90,
        reason="Recognized statement header.",
    )

    assert match.matched is True
    assert match.confidence == 90
    assert match.reason == "Recognized statement header."


@pytest.mark.parametrize(
    "confidence",
    [
        -1,
        101,
    ],
)
def test_processor_match_rejects_invalid_confidence(
    confidence: int,
) -> None:
    """Processor confidence should remain within its valid range."""
    with pytest.raises(
        ValueError,
        match="processor confidence must be between 0 and 100",
    ):
        ProcessorMatch(
            matched=True,
            confidence=confidence,
            reason="test",
        )


def test_processor_match_requires_positive_matched_confidence() -> None:
    """Matched processors should have positive confidence."""
    with pytest.raises(
        ValueError,
        match="matched processors must have positive confidence",
    ):
        ProcessorMatch(
            matched=True,
            confidence=0,
            reason="test",
        )


def test_processor_match_requires_zero_unmatched_confidence() -> None:
    """Unmatched processors should have zero confidence."""
    with pytest.raises(
        ValueError,
        match="unmatched processors must have zero confidence",
    ):
        ProcessorMatch(
            matched=False,
            confidence=50,
            reason="test",
        )


def test_processor_match_requires_reason() -> None:
    """Processor matching should always explain its result."""
    with pytest.raises(
        ValueError,
        match="processor match reason must not be empty",
    ):
        ProcessorMatch(
            matched=False,
            confidence=0,
            reason=" ",
        )
