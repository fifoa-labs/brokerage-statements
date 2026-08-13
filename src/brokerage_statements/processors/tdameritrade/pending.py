"""
src/brokerage_statements/processors/tdameritrade/pending.py

Pending-trade parsing for TD Ameritrade monthly statements.
"""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from brokerage_statements.domain import (
    SourceEvidence,
    StatementSource,
    SymbolSecurity,
    TradeEvent,
    TradeSide,
    TradeStatus,
)

if TYPE_CHECKING:
    from .sections import StatementSections

_PENDING_PATTERN = re.compile(
    r"^(?P<side>BUY|SELL)\s+"
    r".+?\s+"
    r"(?P<account_type>Cash|Margin)\s+"
    r"(?P<symbol>[A-Z][A-Z0-9.-]*)\s+"
    r"(?P<quantity>[\d,]+(?:\.\d+)?)-?\s+"
    r"\$?\s*(?P<price>[\d,]+(?:\.\d+)?)\s+"
    r"(?P<trade_date>\d{2}/\d{2}/\d{2})\s+"
    r"(?P<settle_date>\d{2}/\d{2}/\d{2})\s+"
    r"\$?\s*\(?(?P<amount>[\d,]+(?:\.\d+)?)\)?$"
)


def parse_pending_trades(
    source: StatementSource,
    sections: StatementSections,
    *,
    processor_name: str,
) -> tuple[TradeEvent, ...]:
    """Parse trades pending settlement at statement end."""
    events: list[TradeEvent] = []
    sequence = 1

    for page in sections.pending:
        for line in page.text.splitlines():
            match = _PENDING_PATTERN.match(line.strip())

            if match is None:
                continue

            side = TradeSide(match.group("side").lower())

            evidence = SourceEvidence(
                source=source,
                page=page.number,
                section="Trades Pending Settlement",
                raw_text=line,
                processor=processor_name,
                sequence=sequence,
            )

            events.append(
                TradeEvent(
                    date=_date(match.group("trade_date")),
                    security=SymbolSecurity(
                        match.group("symbol"),
                    ),
                    side=side,
                    status=TradeStatus.PENDING,
                    quantity=_decimal(match.group("quantity")),
                    price=_decimal(match.group("price")),
                    amount=_decimal(match.group("amount")),
                    evidence=(evidence,),
                    settlement_date=_date(
                        match.group("settle_date"),
                    ),
                    position_effect=None,
                )
            )
            sequence += 1

    return tuple(events)


def _date(value: str) -> date:
    """Parse a TD Ameritrade two-digit date."""
    month, day, year = value.split("/")

    return date(
        year=2000 + int(year),
        month=int(month),
        day=int(day),
    )


def _decimal(value: str) -> Decimal:
    """Parse a comma-formatted decimal."""
    return Decimal(value.replace(",", ""))
