"""
src/brokerage_statements/processors/base.py

Core contracts for brokerage statement processors and matching.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from brokerage_statements.domain import (
        Broker,
        ParsedStatement,
        StatementSource,
    )
    from brokerage_statements.text import StatementText


@dataclass(frozen=True, slots=True)
class ProcessorMatch:
    """Describe how strongly a processor matches statement text."""

    matched: bool
    confidence: int
    reason: str

    def __post_init__(self) -> None:
        """Validate processor match metadata."""
        if not 0 <= self.confidence <= 100:  # noqa: PLR2004
            msg = "processor confidence must be between 0 and 100."
            raise ValueError(msg)

        if self.matched and self.confidence == 0:
            msg = "matched processors must have positive confidence."
            raise ValueError(msg)

        if not self.matched and self.confidence != 0:
            msg = "unmatched processors must have zero confidence."
            raise ValueError(msg)

        if not self.reason.strip():
            msg = "processor match reason must not be empty."
            raise ValueError(msg)


class StatementProcessor(Protocol):
    """Contract implemented by brokerage statement processors."""

    @property
    def name(self) -> str:
        """Return the stable processor identifier."""
        ...

    @property
    def broker(self) -> Broker:
        """Return the brokerage institution handled by the processor."""
        ...

    def match(
        self,
        text: StatementText,
    ) -> ProcessorMatch:
        """Return deterministic compatibility information."""
        ...

    def parse(
        self,
        source: StatementSource,
        text: StatementText,
    ) -> ParsedStatement:
        """Parse supported statement text into normalized data."""
        ...
