"""
tests/processors/test_registry.py

Tests for deterministic statement processor selection.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from brokerage_statements.domain import (
    Broker,
    ParsedStatement,
    StatementSource,
)
from brokerage_statements.exceptions import (
    AmbiguousProcessorError,
    UnsupportedStatementError,
)
from brokerage_statements.processors import (
    ProcessorMatch,
    ProcessorRegistry,
)
from brokerage_statements.text import StatementText


@dataclass(frozen=True, slots=True)
class FakeProcessor:
    """Minimal processor used to exercise registry selection."""

    name: str
    broker: Broker
    priority: int
    result: ProcessorMatch

    def match(self, text: StatementText) -> ProcessorMatch:
        """Return the configured match result."""
        del text
        return self.result

    def parse(
        self,
        source: StatementSource,
        text: StatementText,
    ) -> ParsedStatement:
        """Parsing is not needed by registry tests."""
        del source, text
        raise NotImplementedError


def make_processor(
    *,
    name: str,
    matched: bool = True,
    confidence: int = 90,
    priority: int = 10,
) -> FakeProcessor:
    """Create a processor with deterministic match behavior."""
    if not matched:
        confidence = 0

    return FakeProcessor(
        name=name,
        broker=Broker.CHARLES_SCHWAB,
        priority=priority,
        result=ProcessorMatch(
            matched=matched,
            confidence=confidence,
            reason="test match result",
        ),
    )


def test_registry_preserves_processor_order() -> None:
    """Registered processors should retain deterministic order."""
    first = make_processor(name="test.first")
    second = make_processor(name="test.second")

    registry = ProcessorRegistry([first, second])

    assert registry.processors == (first, second)


def test_registry_allows_empty_registry() -> None:
    """A registry may be created before processors are registered."""
    registry = ProcessorRegistry()

    assert registry.processors == ()


def test_registry_selects_only_matching_processor() -> None:
    """A single compatible processor should be selected."""
    processor = make_processor(name="test.one")
    registry = ProcessorRegistry([processor])

    selected = registry.select(StatementText(pages=()))

    assert selected is processor


def test_registry_ignores_unmatched_processors() -> None:
    """Unmatched processors should not participate in selection."""
    unmatched = make_processor(
        name="test.unmatched",
        matched=False,
    )
    matched = make_processor(
        name="test.matched",
        confidence=80,
    )
    registry = ProcessorRegistry([unmatched, matched])

    selected = registry.select(StatementText(pages=()))

    assert selected is matched


def test_registry_rejects_statement_when_registry_is_empty() -> None:
    """An empty registry should not support any statement."""
    registry = ProcessorRegistry()

    with pytest.raises(
        UnsupportedStatementError,
        match="No registered processor supports this statement",
    ):
        registry.select(StatementText(pages=()))


def test_registry_rejects_statement_when_nothing_matches() -> None:
    """A statement with no compatible processor should fail."""
    first = make_processor(
        name="test.first",
        matched=False,
    )
    second = make_processor(
        name="test.second",
        matched=False,
    )
    registry = ProcessorRegistry([first, second])

    with pytest.raises(
        UnsupportedStatementError,
        match="No registered processor supports this statement",
    ):
        registry.select(StatementText(pages=()))


def test_registry_selects_highest_confidence() -> None:
    """Higher match confidence should win processor selection."""
    lower = make_processor(
        name="test.lower",
        confidence=70,
        priority=100,
    )
    higher = make_processor(
        name="test.higher",
        confidence=90,
        priority=1,
    )
    registry = ProcessorRegistry([lower, higher])

    selected = registry.select(StatementText(pages=()))

    assert selected is higher


def test_registry_uses_priority_after_equal_confidence() -> None:
    """Priority should resolve processors with equal confidence."""
    lower_priority = make_processor(
        name="test.lower",
        confidence=90,
        priority=10,
    )
    higher_priority = make_processor(
        name="test.higher",
        confidence=90,
        priority=20,
    )
    registry = ProcessorRegistry([lower_priority, higher_priority])

    selected = registry.select(StatementText(pages=()))

    assert selected is higher_priority


def test_registry_rejects_equivalent_winners() -> None:
    """Equivalent processor winners should be ambiguous."""
    first = make_processor(
        name="test.first",
        confidence=90,
        priority=10,
    )
    second = make_processor(
        name="test.second",
        confidence=90,
        priority=10,
    )
    registry = ProcessorRegistry([first, second])

    with pytest.raises(
        AmbiguousProcessorError,
        match="Ambiguous statement processors: test.first, test.second",  # noqa: RUF043
    ):
        registry.select(StatementText(pages=()))


def test_registry_reports_ambiguous_processors_sorted() -> None:
    """Ambiguous processor names should be reported predictably."""
    second = make_processor(
        name="test.second",
        confidence=90,
        priority=10,
    )
    first = make_processor(
        name="test.first",
        confidence=90,
        priority=10,
    )
    registry = ProcessorRegistry([second, first])

    with pytest.raises(
        AmbiguousProcessorError,
        match="Ambiguous statement processors: test.first, test.second",  # noqa: RUF043
    ):
        registry.select(StatementText(pages=()))


def test_registry_rejects_duplicate_processor_names() -> None:
    """Processor names should uniquely identify implementations."""
    first = make_processor(
        name="test.duplicate",
        confidence=80,
    )
    second = make_processor(
        name="test.duplicate",
        confidence=90,
    )

    with pytest.raises(
        ValueError,
        match="Processor names must be unique: 'test.duplicate'",  # noqa: RUF043
    ):
        ProcessorRegistry([first, second])
