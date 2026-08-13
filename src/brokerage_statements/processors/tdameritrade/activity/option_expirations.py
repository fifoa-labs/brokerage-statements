"""
src/brokerage_statements/processors/tdameritrade/activity/option_expirations.py

Option expiration parsing for TD Ameritrade account activity.
"""

from __future__ import annotations

import re
from datetime import date

from brokerage_statements.domain import (
    OptionExpirationEvent,
    OptionRight,
    OptionSecurity,
    SourceEvidence,
)
from brokerage_statements.exceptions import UnknownActivityError

from ._utils import (
    parse_date,
    parse_unsigned_decimal,
)

_OPTION_EXPIRATION_PATTERN = re.compile(
    r"^(?P<trade_date>\d{2}/\d{2}/\d{2})\s+"
    r"(?P<settle_date>\d{2}/\d{2}/\d{2})\s+"
    r"(?P<account_type>Cash|Margin)\s+"
    r"(?:Delivered|Received)\s+-\s+Other\s+"
    r"(?P<description>.+?)\s+-\s+"
    r"(?P<contracts>[\d,]+(?:\.\d+)?)-?\s+"
    r"0\.00\s+-\s+"
    r"(?P<balance>\(?[\d,]+(?:\.\d+)?\)?)\s+"
    r"(?P<annotation>.+)$",
)

_OPTION_IDENTITY_PATTERN = re.compile(
    r"\b(?P<underlying>[A-Z][A-Z0-9.-]*)\s+"
    r"(?P<month>[A-Z][a-z]{2})\s+"
    r"(?P<day>\d{1,2})\s+"
    r"(?P<year>\d{2})\s+"
    r"(?P<strike>[\d,]+(?:\.\d+)?)\s+"
    r"(?P<right>C|P)\s+"
    r"EXPIRATION\b",
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


def parse_option_expiration(
    row: str,
    evidence: SourceEvidence,
) -> OptionExpirationEvent | None:
    """Parse an expired TD Ameritrade option contract."""
    match = _OPTION_EXPIRATION_PATTERN.match(row)

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

    return OptionExpirationEvent(
        date=parse_date(
            match.group("settle_date"),
        ),
        security=OptionSecurity(
            underlying=identity.group("underlying"),
            expiration=expiration,
            right=right,
            strike=parse_unsigned_decimal(
                identity.group("strike"),
            ),
        ),
        contracts=parse_unsigned_decimal(
            match.group("contracts"),
        ),
        evidence=(evidence,),
    )


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
