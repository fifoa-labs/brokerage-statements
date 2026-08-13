"""
src/brokerage_statements/processors/tdameritrade/activity/trades.py

Settled trade parsing for TD Ameritrade account activity.
"""

from __future__ import annotations

import re

from brokerage_statements.domain import (
    FeeEvent,
    SourceEvidence,
    SymbolSecurity,
    TradeEvent,
    TradeSide,
    TradeStatus,
)
from brokerage_statements.exceptions import UnknownActivityError
from brokerage_statements.reference import resolve_symbol

from ._utils import (
    parse_date,
    parse_unsigned_decimal,
)

_TRADE_PATTERN = re.compile(
    r"^(?P<trade_date>\d{2}/\d{2}/\d{2})\s+"
    r"(?P<settle_date>\d{2}/\d{2}/\d{2})\s+"
    r"(?P<account_type>Cash|Margin)\s+"
    r"(?P<side>Buy|Sell)\s+-\s+"
    r"Securities\s+(?:Purchased|Sold)\s+"
    r"(?P<body>.+)$",
)

_TRADE_VALUES_PATTERN = re.compile(
    r"\b(?P<identifier>[A-Z0-9][A-Z0-9.-]*)\s+"
    r"(?P<quantity>[\d,]+(?:\.\d+)?)-?\s+"
    r"\$?\s*(?P<price>[\d,]+(?:\.\d+)?)\s+"
    r"\$?\s*(?P<amount>\(?[\d,]+(?:\.\d+)?\)?)\s+"
    r"\$?\s*(?P<balance>\(?[\d,]+(?:\.\d+)?\)?)"
)

_REGULATORY_FEE_PATTERN = re.compile(
    r"\bRegulatory Fee\s+\$?\s*"
    r"(?P<amount>[\d,]+(?:\.\d+)?)\b",
)


def parse_trade(
    row: str,
    evidence: SourceEvidence,
) -> tuple[TradeEvent | FeeEvent, ...] | None:
    """Parse a settled buy or sell and any attached fee."""
    match = _TRADE_PATTERN.match(row)

    if match is None:
        return None

    values = _TRADE_VALUES_PATTERN.search(
        match.group("body"),
    )

    if values is None:
        msg = f"Unable to parse TD Ameritrade trade row: {row}"
        raise UnknownActivityError(msg)

    side = TradeSide(match.group("side").lower())

    trade = TradeEvent(
        date=parse_date(
            match.group("trade_date"),
        ),
        security=SymbolSecurity(
            resolve_symbol(
                values.group("identifier"),
            )
        ),
        side=side,
        status=TradeStatus.SETTLED,
        quantity=parse_unsigned_decimal(
            values.group("quantity"),
        ),
        price=parse_unsigned_decimal(
            values.group("price"),
        ),
        amount=parse_unsigned_decimal(
            values.group("amount"),
        ),
        evidence=(evidence,),
        settlement_date=parse_date(
            match.group("settle_date"),
        ),
    )

    fee_match = _REGULATORY_FEE_PATTERN.search(row)

    if fee_match is None:
        return (trade,)

    fee = FeeEvent(
        date=parse_date(
            match.group("settle_date"),
        ),
        amount=parse_unsigned_decimal(
            fee_match.group("amount"),
        ),
        evidence=(evidence,),
        description="Regulatory Fee",
    )

    return trade, fee
