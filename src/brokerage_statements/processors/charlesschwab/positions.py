"""
src/brokerage_statements/processors/charlesschwab/positions.py

Closing-position parsing for Charles Schwab monthly statements.
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


_SECURITY_SECTION_HEADERS = (
    "Positions - Equities",
    "Positions - Other Assets",
)

_DECIMAL_TOKEN = r"-?[\d,]+(?:\.\d+)?"  # noqa: S105

_AMOUNT_TOKEN = rf"(?:{_DECIMAL_TOKEN}|\([\d,]+(?:\.\d+)?\))"

_VALUE_TOKEN = rf"(?:N/A|{_AMOUNT_TOKEN})"

_POSITION_PATTERN = re.compile(
    rf"^(?P<symbol>[A-Z][A-Z0-9.-]*)\s+"
    rf"(?P<description>.+?)\s+"
    rf"(?P<quantity>{_DECIMAL_TOKEN})\s+"
    rf"(?P<price>{_VALUE_TOKEN})\s+"
    rf"(?P<market_value>{_VALUE_TOKEN})\s+"
    rf"(?P<cost_basis>{_VALUE_TOKEN})\s+"
    rf"(?P<gain_loss>{_VALUE_TOKEN})(?:\s+.*)?$"
)

_NUMBER_FIELD_PATTERN = re.compile(rf"(?<!\S){_AMOUNT_TOKEN}(?!\S)")


def parse_positions(  # noqa: C901
    source: StatementSource,
    sections: StatementSections,
    *,
    processor_name: str,
) -> tuple[Position, ...]:
    """Parse closing security positions reported by Schwab."""
    positions: list[Position] = []
    sequence = 1
    active_section: str | None = None
    found_security_section = False

    for page in sections.positions:
        for raw_line in page.text.splitlines():
            line = raw_line.strip()

            if line in _SECURITY_SECTION_HEADERS:
                active_section = line
                found_security_section = True
                continue

            if line == "Transactions - Summary":
                active_section = None
                continue

            if active_section is None:
                continue

            if line.startswith("Total"):
                active_section = None
                continue

            match = _POSITION_PATTERN.match(line)

            if match is None:
                if _looks_like_position_candidate(line):
                    msg = f"Unrecognized Charles Schwab position row: {line}"
                    raise ValueError(msg)

                continue

            evidence = SourceEvidence(
                source=source,
                page=page.number,
                section=active_section,
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

    if not found_security_section:
        msg = "Charles Schwab security position section not found."
        raise ValueError(msg)

    if not positions:
        msg = (
            "Charles Schwab security position sections contain "
            "no parsed positions."
        )
        raise ValueError(msg)

    return tuple(positions)


def _looks_like_position_candidate(
    line: str,
) -> bool:
    """Return whether a line resembles a numeric position row."""
    return len(_NUMBER_FIELD_PATTERN.findall(line)) >= 5  # noqa: PLR2004


def _parse_decimal(value: str) -> Decimal:
    """Parse Schwab comma-formatted decimal notation."""
    return Decimal(
        value.replace(",", ""),
    )
