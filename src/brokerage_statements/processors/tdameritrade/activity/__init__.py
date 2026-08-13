"""
src/brokerage_statements/processors/tdameritrade/activity/__init__.py

Account-activity orchestration for TD Ameritrade monthly statements.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from brokerage_statements.domain import (
    CashTransferEvent,
    FeeEvent,
    IncomeEvent,
    SecurityTransferEvent,
    SourceEvidence,
    StatementSource,
    TradeEvent,
)
from brokerage_statements.exceptions import UnknownActivityError

from .cash import (
    is_known_internal_journal,
    parse_cash_transfer,
)
from .income import parse_income
from .rows import extract_activity_rows
from .trades import parse_trade
from .transfers import (
    is_known_internal_security_transfer,
    parse_security_transfer,
)

if TYPE_CHECKING:
    from brokerage_statements.processors.tdameritrade.sections import (
        StatementSections,
    )

ActivityEvent = (
    TradeEvent
    | CashTransferEvent
    | IncomeEvent
    | FeeEvent
    | SecurityTransferEvent
)


def parse_activity(
    source: StatementSource,
    sections: StatementSections,
    *,
    processor_name: str,
) -> tuple[ActivityEvent, ...]:
    """Parse normalized economic events from account activity."""
    events: list[ActivityEvent] = []

    for row in extract_activity_rows(sections):
        parsed = _parse_row(
            source=source,
            page_number=row.page_number,
            row=row.text,
            processor_name=processor_name,
            sequence=row.sequence,
        )

        events.extend(parsed)

    return tuple(events)


def _parse_row(
    *,
    source: StatementSource,
    page_number: int,
    row: str,
    processor_name: str,
    sequence: int,
) -> tuple[ActivityEvent, ...]:
    """Parse one logical TD Ameritrade activity row."""
    if is_known_internal_journal(row):
        return ()

    if is_known_internal_security_transfer(row):
        return ()

    evidence = SourceEvidence(
        source=source,
        page=page_number,
        section="Account Activity",
        raw_text=row,
        processor=processor_name,
        sequence=sequence,
    )

    trade = parse_trade(
        row,
        evidence,
    )

    if trade is not None:
        return trade

    cash_transfer = parse_cash_transfer(
        row,
        evidence,
    )

    if cash_transfer is not None:
        return (cash_transfer,)

    security_transfer = parse_security_transfer(
        row,
        evidence,
    )

    if security_transfer is not None:
        return (security_transfer,)

    income = parse_income(
        row,
        evidence,
    )

    if income is not None:
        return (income,)

    msg = f"Unknown TD Ameritrade account activity: {row}"
    raise UnknownActivityError(msg)


__all__ = [
    "ActivityEvent",
    "parse_activity",
]
