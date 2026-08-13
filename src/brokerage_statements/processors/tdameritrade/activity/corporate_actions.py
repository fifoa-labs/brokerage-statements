"""
src/brokerage_statements/processors/tdameritrade/activity/corporate_actions.py

Corporate-action parsing for TD Ameritrade account activity.
"""

from __future__ import annotations

import re

from brokerage_statements.domain import (
    CorporateActionEvent,
    CorporateActionType,
    FeeEvent,
    SourceEvidence,
    SymbolSecurity,
)
from brokerage_statements.reference import resolve_symbol

from ._utils import (
    parse_date,
    parse_unsigned_decimal,
)

_REVERSE_SPLIT_DELIVERY_PATTERN = re.compile(
    r"^(?P<trade_date>\d{2}/\d{2}/\d{2})\s+"
    r"(?P<settle_date>\d{2}/\d{2}/\d{2})\s+"
    r"(?P<account_type>Cash|Margin)\s+"
    r"Delivered\s+-\s+Other\s+"
    r"(?P<body>.+?)\s+"
    r"(?P<old_identifier>[A-Z0-9][A-Z0-9.-]*)\s+"
    r"(?P<quantity>[\d,]+(?:\.\d+)?)-?\s+"
    r"0\.00\s+-\s+"
    r"(?P<balance>\(?[\d,]+(?:\.\d+)?\)?)"
    r"(?P<annotation>.+)$",
)

_REVERSE_SPLIT_RECEIPT_PATTERN = re.compile(
    r"^(?P<trade_date>\d{2}/\d{2}/\d{2})\s+"
    r"(?P<settle_date>\d{2}/\d{2}/\d{2})\s+"
    r"(?P<account_type>Cash|Margin)\s+"
    r"Received\s+-\s+Other\s+"
    r"(?P<body>.+?)\s+"
    r"(?P<symbol>[A-Z][A-Z0-9.-]*)\s+"
    r"(?P<quantity>[\d,]+(?:\.\d+)?)\s+"
    r"0\.00\s+-\s+"
    r"(?P<balance>\(?[\d,]+(?:\.\d+)?\)?)"
    r"(?P<annotation>.+)$",
)

_REORGANIZATION_FEE_PATTERN = re.compile(
    r"^(?P<trade_date>\d{2}/\d{2}/\d{2})\s+"
    r"(?P<settle_date>\d{2}/\d{2}/\d{2})\s+"
    r"(?P<account_type>Cash|Margin)\s+"
    r"Journal\s+-\s+Expense\s+"
    r"MANDATORY REORGANIZATION\s+"
    r"(?P<identifier>[A-Z0-9][A-Z0-9.-]*)\s+-\s+"
    r"0\.00\s+"
    r"(?P<amount>\(?[\d,]+(?:\.\d+)?\)?)\s+"
    r"(?P<balance>\(?[\d,]+(?:\.\d+)?\)?)"
    r"(?P<annotation>.*)$",
)

_CASH_IN_LIEU_PATTERN = re.compile(
    r"^(?P<trade_date>\d{2}/\d{2}/\d{2})\s+"
    r"(?P<settle_date>\d{2}/\d{2}/\d{2})\s+"
    r"(?P<account_type>Cash|Margin)\s+"
    r"Div/Int\s+-\s+Securities\s+Sold\s+"
    r"(?P<body>.+?)\s+"
    r"(?P<identifier>[A-Z0-9][A-Z0-9.-]*)\s+-\s+"
    r"0\.00\s+"
    r"(?P<amount>[\d,]+(?:\.\d+)?)\s+"
    r"(?P<balance>\(?[\d,]+(?:\.\d+)?\)?)"
    r"(?P<annotation>.+)$",
)


def is_reverse_split_delivery(row: str) -> bool:
    """Return whether a row delivers old shares for a reverse split."""
    match = _REVERSE_SPLIT_DELIVERY_PATTERN.match(row)

    return match is not None and "REVERSE SPLIT" in match.group("annotation")


def is_reverse_split_receipt(row: str) -> bool:
    """Return whether a row receives new shares from a reverse split."""
    match = _REVERSE_SPLIT_RECEIPT_PATTERN.match(row)

    return match is not None and "REVERSE SPLIT" in match.group("annotation")


def parse_reorganization_fee(
    row: str,
    evidence: SourceEvidence,
) -> FeeEvent | None:
    """Parse a mandatory corporate reorganization fee."""
    match = _REORGANIZATION_FEE_PATTERN.match(row)

    if match is None:
        return None

    resolve_symbol(
        match.group("identifier"),
    )

    return FeeEvent(
        date=parse_date(
            match.group("settle_date"),
        ),
        amount=parse_unsigned_decimal(
            match.group("amount"),
        ),
        evidence=(evidence,),
        description="Mandatory Reorganization Fee",
    )


def parse_cash_in_lieu(
    row: str,
    evidence: SourceEvidence,
) -> CorporateActionEvent | None:
    """Parse cash paid for a fractional share after reorganization."""
    match = _CASH_IN_LIEU_PATTERN.match(row)

    if match is None:
        return None

    annotation = match.group("annotation")

    if "CASH IN LIEU" not in annotation:
        return None

    symbol = resolve_symbol(
        match.group("identifier"),
    )

    return CorporateActionEvent(
        date=parse_date(
            match.group("settle_date"),
        ),
        action_type=CorporateActionType.CASH_IN_LIEU,
        source_security=SymbolSecurity(symbol),
        target_security=None,
        evidence=(evidence,),
        cash=parse_unsigned_decimal(
            match.group("amount"),
        ),
    )
