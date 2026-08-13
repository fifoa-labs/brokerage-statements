"""
src/brokerage_statements/processors/tdameritrade/activity/__init__.py

Account-activity orchestration for TD Ameritrade monthly statements.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from brokerage_statements.domain import (
    CashTransferEvent,
    CorporateActionEvent,
    FeeEvent,
    IncomeEvent,
    OptionExpirationEvent,
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
from .corporate_actions import (
    is_reverse_split_delivery,
    is_reverse_split_receipt,
    parse_cash_in_lieu,
    parse_reorganization_fee,
)
from .income import parse_income
from .option_expirations import parse_option_expiration
from .options import parse_option_trade
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
    | CorporateActionEvent
    | OptionExpirationEvent
)

RowConsumer = Callable[[str], bool]
RowParser = Callable[
    [str, SourceEvidence],
    tuple[ActivityEvent, ...] | ActivityEvent | None,
]

_ROW_CONSUMERS: tuple[RowConsumer, ...] = (
    is_known_internal_journal,
    is_reverse_split_delivery,
    is_reverse_split_receipt,
    is_known_internal_security_transfer,
)

_ROW_PARSERS: tuple[RowParser, ...] = (
    parse_option_trade,
    parse_trade,
    parse_cash_transfer,
    parse_reorganization_fee,
    parse_cash_in_lieu,
    parse_option_expiration,
    parse_security_transfer,
    parse_income,
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
        events.extend(
            _parse_row(
                source=source,
                page_number=row.page_number,
                row=row.text,
                processor_name=processor_name,
                sequence=row.sequence,
            )
        )

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
    if _is_consumed_row(row):
        return ()

    evidence = SourceEvidence(
        source=source,
        page=page_number,
        section="Account Activity",
        raw_text=row,
        processor=processor_name,
        sequence=sequence,
    )

    parsed = _dispatch_row(
        row,
        evidence,
    )

    if parsed is not None:
        return parsed

    msg = f"Unknown TD Ameritrade account activity: {row}"
    raise UnknownActivityError(msg)


def _is_consumed_row(row: str) -> bool:
    """Return whether a known row should produce no normalized event."""
    return any(consumer(row) for consumer in _ROW_CONSUMERS)


def _dispatch_row(
    row: str,
    evidence: SourceEvidence,
) -> tuple[ActivityEvent, ...] | None:
    """Dispatch a logical row to the first compatible activity parser."""
    for parser in _ROW_PARSERS:
        parsed = parser(
            row,
            evidence,
        )

        if parsed is None:
            continue

        if isinstance(parsed, tuple):
            return parsed

        return (parsed,)

    return None


__all__ = [
    "ActivityEvent",
    "parse_activity",
]
