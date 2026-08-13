"""
src/brokerage_statements/processors/tdameritrade/monthly_2020.py

Processor for the TD Ameritrade monthly statement grammar.
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
from .positions import parse_positions
from .sections import extract_sections

if TYPE_CHECKING:
    from brokerage_statements.text import StatementText

_PROCESSOR_NAME = "tdameritrade.monthly_2020"

_REQUIRED_MARKERS = (
    "Statement Reporting Period:",
    "Statement for Account #",
    "Portfolio Summary",
    "Account Activity",
)

_TRANSITION_MARKERS = (
    "IDA FEATURE DURING TRANSITION",
    "TDA TO CS&CO TRANSFER",
)


class Monthly2020Processor:
    """Process the TD Ameritrade monthly statement grammar."""

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
        """Return compatibility with the monthly TD grammar."""
        is_transition = all(
            marker in text.text for marker in _TRANSITION_MARKERS
        )

        if is_transition:
            return ProcessorMatch(
                matched=False,
                confidence=0,
                reason=(
                    "TD Ameritrade transition statement requires "
                    "the transition processor."
                ),
            )

        missing = tuple(
            marker for marker in _REQUIRED_MARKERS if marker not in text.text
        )

        if missing:
            return ProcessorMatch(
                matched=False,
                confidence=0,
                reason=(
                    "Missing TD Ameritrade monthly markers: "
                    + ", ".join(missing)
                ),
            )

        return ProcessorMatch(
            matched=True,
            confidence=100,
            reason="Recognized TD Ameritrade monthly statement grammar.",
        )

    def parse(
        self,
        source: StatementSource,
        text: StatementText,
    ) -> ParsedStatement:
        """Parse a TD Ameritrade monthly statement."""
        identity = parse_statement_identity(text)
        sections = extract_sections(text)

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
        positions = parse_positions(
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
            positions=positions,
        )
