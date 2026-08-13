"""
src/brokerage_statements/processors/tdameritrade/activity.py

Settled account-activity parsing for TD Ameritrade monthly statements.
"""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from brokerage_statements.domain import (
    CashTransferEvent,
    CashTransferType,
    FeeEvent,
    IncomeEvent,
    IncomeType,
    SecurityTransferDirection,
    SecurityTransferEvent,
    SourceEvidence,
    StatementSource,
    SymbolSecurity,
    TradeEvent,
    TradeSide,
    TradeStatus,
)
from brokerage_statements.exceptions import UnknownActivityError
from brokerage_statements.reference import resolve_symbol

if TYPE_CHECKING:
    from .sections import StatementSections

ActivityEvent = (
    TradeEvent
    | CashTransferEvent
    | IncomeEvent
    | FeeEvent
    | SecurityTransferEvent
)

_ROW_START_PATTERN = re.compile(
    r"^\d{2}/\d{2}/\d{2}\s+\d{2}/\d{2}/\d{2}\s+",
)

_TRADE_PATTERN = re.compile(
    r"^(?P<trade_date>\d{2}/\d{2}/\d{2})\s+"
    r"(?P<settle_date>\d{2}/\d{2}/\d{2})\s+"
    r"(?P<account_type>Cash|Margin)\s+"
    r"(?P<side>Buy|Sell)\s+-\s+"
    r"Securities\s+(?:Purchased|Sold)\s+"
    r"(?P<body>.+)$",
)

_CASH_TRANSFER_PATTERN = re.compile(
    r"^(?P<trade_date>\d{2}/\d{2}/\d{2})\s+"
    r"(?P<settle_date>\d{2}/\d{2}/\d{2})\s+"
    r"(?P<account_type>Cash|Margin)"
    r"(?:\s+Journal)?\s+-\s+"
    r"Funds\s+(?P<direction>Deposited|Disbursed)\s+"
    r"(?P<body>.+)$",
)

_SECURITY_TRANSFER_PATTERN = re.compile(
    r"^(?P<trade_date>\d{2}/\d{2}/\d{2})\s+"
    r"(?P<settle_date>\d{2}/\d{2}/\d{2})\s+"
    r"(?P<account_type>Cash|Margin)\s+"
    r"(?P<direction>Received|Delivered)\s+-\s+Other\s+"
    r"(?P<body>.+)$",
)

_INCOME_PATTERN = re.compile(
    r"^(?P<trade_date>\d{2}/\d{2}/\d{2})\s+"
    r"(?P<settle_date>\d{2}/\d{2}/\d{2})\s+"
    r"(?P<account_type>Cash|Margin)\s+"
    r"Div/Int\s+-\s+Income\s+"
    r"(?P<body>.+)$",
)

_INTERNAL_JOURNAL_PATTERN = re.compile(
    r"^\d{2}/\d{2}/\d{2}\s+"
    r"\d{2}/\d{2}/\d{2}\s+"
    r"(?:Cash|Margin)\s+Journal\s+-\s+Other\s+",
)

_TRADE_VALUES_PATTERN = re.compile(
    r"\b(?P<identifier>[A-Z0-9][A-Z0-9.-]*)\s+"
    r"(?P<quantity>[\d,]+(?:\.\d+)?)-?\s+"
    r"\$?\s*(?P<price>[\d,]+(?:\.\d+)?)\s+"
    r"\$?\s*(?P<amount>\(?[\d,]+(?:\.\d+)?\)?)\s+"
    r"\$?\s*(?P<balance>\(?[\d,]+(?:\.\d+)?\)?)"
)

_SECURITY_TRANSFER_VALUES_PATTERN = re.compile(
    r"\b(?P<identifier>[A-Z0-9][A-Z0-9.-]*)\s+"
    r"(?P<quantity>[\d,]+(?:\.\d+)?)-?\s+"
    r"\$?\s*0\.00\b",
)

_REGULATORY_FEE_PATTERN = re.compile(
    r"\bRegulatory Fee\s+\$?\s*"
    r"(?P<amount>[\d,]+(?:\.\d+)?)\b",
)

_TRAILING_MONEY_PATTERN = re.compile(
    r"\$?\s*(?P<value>\(?[\d,]+(?:\.\d+)?\)?)"
)

_KNOWN_INTERNAL_JOURNAL_MARKERS = (
    "MOVE CASH BALANCE TO",
    "PURCHASE FDIC INSURED",
    "REDEMPTION FDIC INSURED",
    "TRANSFER FROM",
)

_KNOWN_INTERNAL_SECURITY_TRANSFER_MARKERS = (
    "TRANSFER FROM ",
    "TRANSFER TO ",
)


def parse_activity(
    source: StatementSource,
    sections: StatementSections,
    *,
    processor_name: str,
) -> tuple[ActivityEvent, ...]:
    """Parse normalized economic events from account activity."""
    events: list[ActivityEvent] = []

    for sequence, (page_number, row) in enumerate(
        _activity_rows(sections),
        start=1,
    ):
        parsed = _parse_row(
            source=source,
            page_number=page_number,
            row=row,
            processor_name=processor_name,
            sequence=sequence,
        )

        events.extend(parsed)

    return tuple(events)


def _activity_rows(
    sections: StatementSections,
) -> tuple[tuple[int, str], ...]:
    """Join wrapped account-activity lines into logical rows."""
    rows: list[tuple[int, str]] = []

    for page in sections.activity:
        current: list[str] = []

        for raw_line in page.text.splitlines():
            line = raw_line.strip()

            if _ROW_START_PATTERN.match(line):
                if current:
                    rows.append(
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
                rows.append(
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
            rows.append(
                (
                    page.number,
                    " ".join(current),
                )
            )

    return tuple(rows)


def _parse_row(
    *,
    source: StatementSource,
    page_number: int,
    row: str,
    processor_name: str,
    sequence: int,
) -> tuple[ActivityEvent, ...]:
    """Parse one logical TD Ameritrade activity row."""
    if _is_known_internal_journal(row):
        return ()

    if _is_known_internal_security_transfer(row):
        return ()

    evidence = SourceEvidence(
        source=source,
        page=page_number,
        section="Account Activity",
        raw_text=row,
        processor=processor_name,
        sequence=sequence,
    )

    trade = _parse_trade(
        row,
        evidence,
    )

    if trade is not None:
        return trade

    cash_transfer = _parse_cash_transfer(
        row,
        evidence,
    )

    if cash_transfer is not None:
        return (cash_transfer,)

    security_transfer = _parse_security_transfer(
        row,
        evidence,
    )

    if security_transfer is not None:
        return (security_transfer,)

    income = _parse_income(
        row,
        evidence,
    )

    if income is not None:
        return (income,)

    msg = f"Unknown TD Ameritrade account activity: {row}"
    raise UnknownActivityError(msg)


def _parse_trade(
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
        date=_parse_date(
            match.group("trade_date"),
        ),
        security=SymbolSecurity(
            resolve_symbol(
                values.group("identifier"),
            )
        ),
        side=side,
        status=TradeStatus.SETTLED,
        quantity=_parse_unsigned_decimal(
            values.group("quantity"),
        ),
        price=_parse_unsigned_decimal(
            values.group("price"),
        ),
        amount=_parse_unsigned_decimal(
            values.group("amount"),
        ),
        evidence=(evidence,),
        settlement_date=_parse_date(
            match.group("settle_date"),
        ),
    )

    fee_match = _REGULATORY_FEE_PATTERN.search(row)

    if fee_match is None:
        return (trade,)

    fee = FeeEvent(
        date=_parse_date(
            match.group("settle_date"),
        ),
        amount=_parse_unsigned_decimal(
            fee_match.group("amount"),
        ),
        evidence=(evidence,),
        description="Regulatory Fee",
    )

    return trade, fee


def _parse_cash_transfer(
    row: str,
    evidence: SourceEvidence,
) -> CashTransferEvent | None:
    """Parse deposited or disbursed funds."""
    match = _CASH_TRANSFER_PATTERN.match(row)

    if match is None:
        return None

    amounts = _money_values(
        match.group("body"),
    )

    if len(amounts) < 2:  # noqa: PLR2004
        msg = f"Unable to parse TD Ameritrade cash transfer row: {row}"
        raise UnknownActivityError(msg)

    transfer_type = (
        CashTransferType.DEPOSIT
        if match.group("direction") == "Deposited"
        else CashTransferType.WITHDRAWAL
    )

    return CashTransferEvent(
        date=_parse_date(
            match.group("settle_date"),
        ),
        transfer_type=transfer_type,
        amount=_absolute(amounts[-2]),
        evidence=(evidence,),
    )


def _parse_security_transfer(
    row: str,
    evidence: SourceEvidence,
) -> SecurityTransferEvent | None:
    """Parse a security delivered into or out of the account."""
    match = _SECURITY_TRANSFER_PATTERN.match(row)

    if match is None:
        return None

    values = _SECURITY_TRANSFER_VALUES_PATTERN.search(
        match.group("body"),
    )

    if values is None:
        msg = f"Unable to parse TD Ameritrade security transfer row: {row}"
        raise UnknownActivityError(msg)

    direction = (
        SecurityTransferDirection.IN
        if match.group("direction") == "Received"
        else SecurityTransferDirection.OUT
    )

    return SecurityTransferEvent(
        date=_parse_date(
            match.group("settle_date"),
        ),
        security=SymbolSecurity(
            resolve_symbol(
                values.group("identifier"),
            )
        ),
        direction=direction,
        quantity=_parse_unsigned_decimal(
            values.group("quantity"),
        ),
        evidence=(evidence,),
    )


def _parse_income(
    row: str,
    evidence: SourceEvidence,
) -> IncomeEvent | None:
    """Parse brokerage interest income."""
    match = _INCOME_PATTERN.match(row)

    if match is None:
        return None

    amounts = _money_values(
        match.group("body"),
    )

    if len(amounts) < 2:  # noqa: PLR2004
        msg = f"Unable to parse TD Ameritrade income row: {row}"
        raise UnknownActivityError(msg)

    return IncomeEvent(
        date=_parse_date(
            match.group("settle_date"),
        ),
        income_type=IncomeType.INTEREST,
        amount=_absolute(amounts[-2]),
        evidence=(evidence,),
    )


def _is_known_internal_journal(row: str) -> bool:
    """Return whether a row is a known internal cash movement."""
    if _INTERNAL_JOURNAL_PATTERN.match(row) is None:
        return False

    return any(marker in row for marker in _KNOWN_INTERNAL_JOURNAL_MARKERS)


def _is_known_internal_security_transfer(
    row: str,
) -> bool:
    """Return whether a security transfer stays inside the TD account."""
    match = _SECURITY_TRANSFER_PATTERN.match(row)

    if match is None:
        return False

    body = match.group("body")

    return any(
        marker in body for marker in _KNOWN_INTERNAL_SECURITY_TRANSFER_MARKERS
    )


def _money_values(value: str) -> tuple[Decimal, ...]:
    """Return monetary values appearing in source order."""
    return tuple(
        _parse_decimal(match.group("value"))
        for match in _TRAILING_MONEY_PATTERN.finditer(value)
    )


def _parse_unsigned_decimal(value: str) -> Decimal:
    """Parse a decimal magnitude regardless of statement sign notation."""
    return _absolute(
        _parse_decimal(value),
    )


def _parse_decimal(value: str) -> Decimal:
    """Parse TD Ameritrade money and quantity notation."""
    normalized = value.strip().replace("$", "").replace(",", "")

    negative = normalized.startswith("(") and normalized.endswith(")")

    if negative:
        normalized = normalized[1:-1]

    result = Decimal(normalized)

    if negative:
        return -result

    return result


def _absolute(value: Decimal) -> Decimal:
    """Return the non-negative magnitude of a decimal."""
    return abs(value)


def _parse_date(value: str) -> date:
    """Parse a TD Ameritrade two-digit activity date."""
    month_text, day_text, year_text = value.split("/")

    return date(
        year=2000 + int(year_text),
        month=int(month_text),
        day=int(day_text),
    )


def _is_page_footer(line: str) -> bool:
    """Return whether a line is a TD statement page footer."""
    return bool(
        re.fullmatch(
            r"page\s+\d+\s+of\s+\d+",
            line,
            flags=re.IGNORECASE,
        )
    )
