"""
src/brokerage_statements/processors/registry.py

Deterministic registration and selection of statement processors.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from brokerage_statements.exceptions import (
    AmbiguousProcessorError,
    UnsupportedStatementError,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

    from brokerage_statements.domain import Broker
    from brokerage_statements.text import StatementText

    from .base import StatementProcessor


class ProcessorRegistry:
    """Store processors and select one compatible broker processor."""

    def __init__(
        self,
        processors: Iterable[StatementProcessor] = (),
    ) -> None:
        """Create a registry from an ordered processor collection."""
        self._processors = tuple(processors)
        self._validate_unique_names()

    @property
    def processors(self) -> tuple[StatementProcessor, ...]:
        """Return registered processors in deterministic order."""
        return self._processors

    def select(
        self,
        text: StatementText,
        *,
        broker: Broker,
    ) -> StatementProcessor:
        """Return the unique highest-confidence processor."""
        processors = tuple(
            processor
            for processor in self._processors
            if processor.broker is broker
        )

        if not processors:
            msg = f"No registered processors for broker {broker.value!r}."
            raise UnsupportedStatementError(msg)

        candidates = [
            (processor, match)
            for processor in processors
            if (match := processor.match(text)).matched
        ]

        if not candidates:
            msg = (
                "No registered processor supports this statement "
                f"for broker {broker.value!r}."
            )
            raise UnsupportedStatementError(msg)

        best_confidence = max(match.confidence for _, match in candidates)

        winners = [
            processor
            for processor, match in candidates
            if match.confidence == best_confidence
        ]

        if len(winners) != 1:
            names = ", ".join(sorted(processor.name for processor in winners))
            msg = f"Ambiguous statement processors: {names}."
            raise AmbiguousProcessorError(msg)

        return winners[0]

    def _validate_unique_names(self) -> None:
        """Require unique processor names within the registry."""
        names: set[str] = set()

        for processor in self._processors:
            if processor.name in names:
                msg = f"Processor names must be unique: {processor.name!r}."
                raise ValueError(msg)

            names.add(processor.name)
