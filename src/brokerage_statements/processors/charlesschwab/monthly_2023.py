"""
src/brokerage_statements/processors/charlesschwab/monthly_2023.py

Processor for the observed Charles Schwab monthly statement grammar.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from brokerage_statements.domain import (
    Broker,
    ParsedStatement,
    StatementSource,
)
from brokerage_statements.processors.base import ProcessorMatch

from .activity import extract_activity_rows
from .identity import parse_statement_identity
from .positions import parse_positions
from .sections import extract_sections

if TYPE_CHECKING:
    from brokerage_statements.text import StatementText


_PROCESSOR_NAME = "charlesschwab.monthly_2023"

_REQUIRED_MARKERS = (
    "Schwab One® Account of",
    "Account Summary",
    "Positions - Summary",
    "Transactions - Summary",
)


class Monthly2023Processor:
    """Process the observed Charles Schwab monthly statement grammar."""

    @property
    def name(self) -> str:
        """Return the stable processor identifier."""
        return _PROCESSOR_NAME

    @property
    def broker(self) -> Broker:
        """Return the brokerage institution."""
        return Broker.CHARLES_SCHWAB

    def match(
        self,
        text: StatementText,
    ) -> ProcessorMatch:
        """Return compatibility with the Schwab monthly grammar."""
        missing = tuple(
            marker for marker in _REQUIRED_MARKERS if marker not in text.text
        )

        if missing:
            return ProcessorMatch(
                matched=False,
                confidence=0,
                reason=(
                    "Missing Charles Schwab monthly markers: "
                    + ", ".join(missing)
                ),
            )

        return ProcessorMatch(
            matched=True,
            confidence=100,
            reason="Recognized Charles Schwab monthly statement grammar.",
        )

    def parse(
        self,
        source: StatementSource,
        text: StatementText,
    ) -> ParsedStatement:
        """Parse a Charles Schwab monthly statement."""
        parse_statement_identity(text)
        sections = extract_sections(text)

        parse_positions(
            source,
            sections,
            processor_name=self.name,
        )
        extract_activity_rows(sections)

        msg = (
            "Charles Schwab monthly activity normalization is not implemented."
        )
        raise NotImplementedError(msg)
