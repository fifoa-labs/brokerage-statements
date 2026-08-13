"""
src/brokerage_statements/processors/tdameritrade/activity/options.py

Option trade parsing for TD Ameritrade account activity.
"""

from __future__ import annotations

import re
from datetime import date

from brokerage_statements.domain import (
    FeeEvent,
    OptionRight,
    OptionSecurity,
    PositionEffect,
    SourceEvidence,
    TradeEvent,
    TradeSide,
    TradeStatus,
)
from brokerage_statements.exceptions import UnknownActivityError

from ._utils import (
    parse_date,
    parse_unsigned_decimal,
)

_OPTION_TRADE_PATTERN = re.compile(
    r"^(?P<trade_date>\d{2}/\d{2}/\d{2})\s+"
    r"(?P<settle_date>\d{2}/\d{2}/\d{2})\s+"
    r"(?P<account_type>Cash|Margin)\s+"
    r"(?P<side>Buy|Sell)\s+-\s+"
    r"Securities\s+(?:Purchased|Sold)\s+"
    r"(?P<description>.+?)\s+-\s+"
    r"(?P<contracts>[\d,]+(?:\.\d+)?)-?\s+"
    r"\$?\s*(?P<price>[\d,]+(?:\.\d+)?)\s+"
    r"\$?\s*(?P<amount>\(?[\d,]+(?:\.\d+)?\)?)\s+"
    r"\$?\s*(?P<balance>\(?[\d,]+(?:\.\d+)?\)?)\s+"
    r"(?P<annotation>.+)$",
)

_OPTION_IDENTITY_PATTERN = re.compile(
    r"\b(?P<underlying>[A-Z][A-Z0-9.-]*)\s+"
    r"(?P<month>[A-Z][a-z]{2})\s+"
    r"(?P<day>\d{1,2})\s+"
    r"(?P<year>\d{2})\s+"
    r"(?P<strike>[\d,]+(?:\.\d+)?)\s+"
    r"(?P<right>C|P)\s+"
    r"TO\s+(?P<effect>OPEN|CLOSE)\b",
)

_COMMISSION_FEE_PATTERN = re.compile(
    r"\bCommission/Fee\s+\$?\s*"
    r"(?P<amount>[\d,]+(?:\.\d+)?)\b",
)

_REGULATORY_FEE_PATTERN = re.compile(
    r"\bRegulatory Fee\s+\$?\s*"
    r"(?P<amount>[\d,]+(?:\.\d+)?)\b",
)

_MONTHS = {
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Aug": 8,
    "Sep": 9,
    "Oct": 10,
    "Nov": 11,
    "Dec": 12,
}


def parse_option_trade(
    row: str,
    evidence: SourceEvidence,
) -> tuple[TradeEvent | FeeEvent, ...] | None:
    """Parse a TD Ameritrade option trade and attached fees."""
    match = _OPTION_TRADE_PATTERN.match(row)

    if match is None:
        return None

    identity = _OPTION_IDENTITY_PATTERN.search(
        match.group("annotation"),
    )

    if identity is None:
        return None

    expiration = _parse_expiration(
        month=identity.group("month"),
        day=identity.group("day"),
        year=identity.group("year"),
    )

    right = (
        OptionRight.CALL if identity.group("right") == "C" else OptionRight.PUT
    )

    position_effect = (
        PositionEffect.OPEN
        if identity.group("effect") == "OPEN"
        else PositionEffect.CLOSE
    )

    trade = TradeEvent(
        date=parse_date(
            match.group("trade_date"),
        ),
        security=OptionSecurity(
            underlying=identity.group("underlying"),
            expiration=expiration,
            right=right,
            strike=parse_unsigned_decimal(
                identity.group("strike"),
            ),
        ),
        side=TradeSide(
            match.group("side").lower(),
        ),
        status=TradeStatus.SETTLED,
        position_effect=position_effect,
        quantity=parse_unsigned_decimal(
            match.group("contracts"),
        ),
        price=parse_unsigned_decimal(
            match.group("price"),
        ),
        amount=parse_unsigned_decimal(
            match.group("amount"),
        ),
        evidence=(evidence,),
        settlement_date=parse_date(
            match.group("settle_date"),
        ),
    )

    events: list[TradeEvent | FeeEvent] = [trade]

    commission = _COMMISSION_FEE_PATTERN.search(row)

    if commission is not None:
        events.append(
            FeeEvent(
                date=parse_date(
                    match.group("settle_date"),
                ),
                amount=parse_unsigned_decimal(
                    commission.group("amount"),
                ),
                evidence=(evidence,),
                description="Commission/Fee",
            )
        )

    regulatory_fee = _REGULATORY_FEE_PATTERN.search(row)

    if regulatory_fee is not None:
        events.append(
            FeeEvent(
                date=parse_date(
                    match.group("settle_date"),
                ),
                amount=parse_unsigned_decimal(
                    regulatory_fee.group("amount"),
                ),
                evidence=(evidence,),
                description="Regulatory Fee",
            )
        )

    return tuple(events)


def _parse_expiration(
    *,
    month: str,
    day: str,
    year: str,
) -> date:
    """Parse TD Ameritrade option expiration notation."""
    try:
        month_number = _MONTHS[month]
    except KeyError as exc:
        msg = f"Unsupported TD Ameritrade option month: {month!r}."
        raise UnknownActivityError(msg) from exc

    return date(
        year=2000 + int(year),
        month=month_number,
        day=int(day),
    )
