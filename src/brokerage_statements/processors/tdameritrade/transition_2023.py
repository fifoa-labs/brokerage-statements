"""
src/brokerage_statements/processors/tdameritrade/transition_2023.py

Processor for final TD Ameritrade statements transitioning to Charles Schwab.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from brokerage_statements.domain import (
    Broker,
    ParsedStatement,
    StatementPeriod,
    StatementSource,
)
from brokerage_statements.processors.base import ProcessorMatch

from .activity import parse_activity
from .identity import parse_statement_identity
from .pending import parse_pending_trades
from .sections import extract_sections

if TYPE_CHECKING:
    from brokerage_statements.text import StatementText

_PROCESSOR_NAME = "tdameritrade.transition_2023"

_REQUIRED_MARKERS = (
    "Statement Reporting Period:",
    "Statement for Account #",
    "Portfolio Summary",
    "Account Activity",
    "TDA TO CS&CO TRANSFER",
    "IDA FEATURE DURING TRANSITION",
)


class Transition2023Processor:
    """Process final TD Ameritrade statements transitioning to Schwab."""

    @property
    def name(self) -> str:
        """Return the stable processor identifier."""
        return _PROCESSOR_NAME

    @property
    def broker(self) -> Broker:
        """Return the brokerage institution."""
        return Broker.TD_AMERITRADE

    def match(
        self,
        text: StatementText,
    ) -> ProcessorMatch:
        """Return compatibility with the TD-to-Schwab transition grammar."""
        missing = tuple(
            marker for marker in _REQUIRED_MARKERS if marker not in text.text
        )

        if missing:
            return ProcessorMatch(
                matched=False,
                confidence=0,
                reason=(
                    "Missing TD Ameritrade transition markers: "
                    + ", ".join(missing)
                ),
            )

        return ProcessorMatch(
            matched=True,
            confidence=100,
            reason=(
                "Recognized TD Ameritrade Charles Schwab "
                "transition statement grammar."
            ),
        )

    def parse(
        self,
        source: StatementSource,
        text: StatementText,
    ) -> ParsedStatement:
        """Parse a TD Ameritrade transition statement."""
        identity = parse_statement_identity(text)
        sections = extract_sections(
            text,
            require_positions=False,
        )

        settled_events = parse_activity(
            source,
            sections,
            processor_name=self.name,
        )
        pending_events = parse_pending_trades(
            source,
            sections,
            processor_name=self.name,
        )

        return ParsedStatement(
            source=source,
            broker=self.broker,
            processor_name=self.name,
            account_id=identity.account_id,
            currency="USD",
            period=StatementPeriod(
                start=identity.start,
                end=identity.end,
            ),
            events=settled_events + pending_events,
            positions=(),
        )
