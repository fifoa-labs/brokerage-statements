"""
src/brokerage_statements/processors/tdameritrade/positions.py

Closing-position parsing for TD Ameritrade monthly statements.
"""

from __future__ import annotations

import re
from decimal import Decimal
from typing import TYPE_CHECKING

from brokerage_statements.domain import (
    Position,
    SourceEvidence,
    StatementSource,
    SymbolSecurity,
)

if TYPE_CHECKING:
    from .sections import StatementSections

_POSITION_PATTERN = re.compile(
    r"^(?:.+?\s+)?"
    r"(?P<symbol>[A-Z][A-Z0-9.-]*)\s+"
    r"(?P<quantity>[\d,]+(?:\.\d+)?)\s+"
    r"\$?\s*(?P<price>NA|[\d,]+(?:\.\d+)?)\s+"
    r"\$?\s*(?P<market_value>NA|[\d,]+(?:\.\d+)?)\s+"
    r"(?P<purchase_date>\d{2}/\d{2}/\d{2})\s+"
    r"\$?\s*(?P<cost_basis>[\d,]+(?:\.\d+)?)\b"
)


def parse_positions(
    source: StatementSource,
    sections: StatementSections,
    *,
    processor_name: str,
) -> tuple[Position, ...]:
    """Parse closing positions reported by the statement."""
    positions: list[Position] = []
    sequence = 1

    for page in sections.positions:
        for raw_line in page.text.splitlines():
            line = raw_line.strip()
            match = _POSITION_PATTERN.match(line)

            if match is None:
                continue

            evidence = SourceEvidence(
                source=source,
                page=page.number,
                section="Account Positions",
                raw_text=line,
                processor=processor_name,
                sequence=sequence,
            )

            positions.append(
                Position(
                    security=SymbolSecurity(
                        match.group("symbol"),
                    ),
                    quantity=_parse_decimal(
                        match.group("quantity"),
                    ),
                    evidence=evidence,
                )
            )
            sequence += 1

    return tuple(positions)


def _parse_decimal(value: str) -> Decimal:
    """Parse TD Ameritrade comma-formatted decimal notation."""
    return Decimal(
        value.replace(",", ""),
    )
