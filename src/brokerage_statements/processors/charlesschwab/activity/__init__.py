"""
src/brokerage_statements/processors/charlesschwab/activity/__init__.py

Account-activity orchestration for Charles Schwab monthly statements.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from brokerage_statements.domain import (
    CashTransferEvent,
    CorporateActionEvent,
    IncomeEvent,
    SecurityTransferEvent,
    SourceEvidence,
    StatementSource,
)
from brokerage_statements.exceptions import UnknownActivityError

from .cash import parse_cash_transfer
from .corporate_actions import (
    CorporateActionMatch,
    parse_corporate_action,
)
from .income import parse_income
from .rows import (
    ActivityRow,
    extract_activity_rows,
)
from .transfers import parse_security_transfer

if TYPE_CHECKING:
    from brokerage_statements.processors.charlesschwab.sections import (
        StatementSections,
    )


ActivityEvent = (
    CashTransferEvent
    | CorporateActionEvent
    | IncomeEvent
    | SecurityTransferEvent
)


def parse_activity(
    source: StatementSource,
    sections: StatementSections,
    *,
    processor_name: str,
    year: int,
) -> tuple[ActivityEvent, ...]:
    """Parse normalized economic events from Schwab activity."""
    rows = extract_activity_rows(sections)
    events: list[ActivityEvent] = []
    index = 0

    while index < len(rows):
        corporate_action = _parse_grouped_corporate_action(
            source=source,
            rows=rows[index:],
            processor_name=processor_name,
            year=year,
        )

        if corporate_action is not None:
            events.append(corporate_action.event)
            index += corporate_action.consumed_rows
            continue

        events.append(
            _parse_row(
                source=source,
                row=rows[index],
                processor_name=processor_name,
                year=year,
            )
        )
        index += 1

    return tuple(events)


def _parse_grouped_corporate_action(
    *,
    source: StatementSource,
    rows: tuple[ActivityRow, ...],
    processor_name: str,
    year: int,
) -> CorporateActionMatch | None:
    """Parse a corporate action spanning one or more logical rows."""
    if not rows:
        return None

    first = rows[0]

    is_reverse_split = (
        first.category == "Other Activity" and "ReverseSplit " in first.text
    )
    is_position_adjustment = (
        first.category == "Other Activity" and "AdjustPosition " in first.text
    )
    is_redemption = first.category == "Redemption"

    if (
        not is_reverse_split
        and not is_position_adjustment
        and not is_redemption
    ):
        return None

    evidence = tuple(
        SourceEvidence(
            source=source,
            page=row.page_number,
            section="Transaction Details",
            raw_text=row.text,
            processor=processor_name,
            sequence=row.sequence,
        )
        for row in rows[:2]
    )

    return parse_corporate_action(
        rows,
        evidence,
        year=year,
    )


def _parse_row(
    *,
    source: StatementSource,
    row: ActivityRow,
    processor_name: str,
    year: int,
) -> ActivityEvent:
    """Parse exactly one logical Charles Schwab activity row."""
    evidence = SourceEvidence(
        source=source,
        page=row.page_number,
        section="Transaction Details",
        raw_text=row.text,
        processor=processor_name,
        sequence=row.sequence,
    )

    event = _dispatch_row(
        row,
        evidence,
        year=year,
    )

    if event is not None:
        return event

    msg = f"Unknown Charles Schwab account activity: {row.text}"
    raise UnknownActivityError(msg)


def _dispatch_row(
    row: ActivityRow,
    evidence: SourceEvidence,
    *,
    year: int,
) -> ActivityEvent | None:
    """Dispatch a row to the first compatible focused parser."""
    cash = parse_cash_transfer(
        row,
        evidence,
        year=year,
    )

    if cash is not None:
        return cash

    transfer = parse_security_transfer(
        row,
        evidence,
        year=year,
    )

    if transfer is not None:
        return transfer

    return parse_income(
        row,
        evidence,
        year=year,
    )


__all__ = [
    "ActivityEvent",
    "ActivityRow",
    "extract_activity_rows",
    "parse_activity",
]
