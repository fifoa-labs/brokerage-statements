"""
src/brokerage_statements/processors/tdameritrade/activity/rows.py

Logical row extraction for TD Ameritrade account activity.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from brokerage_statements.processors.tdameritrade.sections import (
        StatementSections,
    )

_ROW_START_PATTERN = re.compile(
    r"^\d{2}/\d{2}/\d{2}\s+\d{2}/\d{2}/\d{2}\s+",
)

_PAGE_FOOTER_PATTERN = re.compile(
    r"page\s+\d+\s+of\s+\d+",
    flags=re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class ActivityRow:
    """One logical account-activity row and its source location."""

    page_number: int
    sequence: int
    text: str


def extract_activity_rows(
    sections: StatementSections,
) -> tuple[ActivityRow, ...]:
    """Join wrapped account-activity lines into logical rows."""
    extracted: list[tuple[int, str]] = []

    for page in sections.activity:
        current: list[str] = []

        for raw_line in page.text.splitlines():
            line = raw_line.strip()

            if _ROW_START_PATTERN.match(line):
                if current:
                    extracted.append(
                        (
                            page.number,
                            " ".join(current),
                        )
                    )

                current = [line]
                continue

            if not current:
                continue

            if line.startswith("Closing Balance"):
                extracted.append(
                    (
                        page.number,
                        " ".join(current),
                    )
                )
                current = []
                continue

            if _is_page_footer(line):
                continue

            current.append(line)

        if current:
            extracted.append(
                (
                    page.number,
                    " ".join(current),
                )
            )

    return tuple(
        ActivityRow(
            page_number=page_number,
            sequence=sequence,
            text=text,
        )
        for sequence, (page_number, text) in enumerate(
            extracted,
            start=1,
        )
    )


def _is_page_footer(line: str) -> bool:
    """Return whether a line is a TD statement page footer."""
    return _PAGE_FOOTER_PATTERN.fullmatch(line) is not None
