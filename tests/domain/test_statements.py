"""
tests/domain/test_statements.py

Tests for statement-level brokerage domain models.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from brokerage_statements.domain import (
    Broker,
    CashTransferEvent,
    CashTransferType,
    ParsedStatement,
    Position,
    SourceEvidence,
    StatementPeriod,
    StatementSource,
    SymbolSecurity,
)


def test_statement_period_preserves_valid_dates() -> None:
    """Valid statement periods should preserve their dates."""
    period = StatementPeriod(
        start=date(2026, 1, 1),
        end=date(2026, 1, 31),
    )

    assert period.start == date(2026, 1, 1)
    assert period.end == date(2026, 1, 31)


def test_statement_period_allows_single_day() -> None:
    """Statement periods may begin and end on the same date."""
    day = date(2026, 1, 31)

    period = StatementPeriod(start=day, end=day)

    assert period.start == day
    assert period.end == day


def test_statement_period_rejects_reversed_dates() -> None:
    """Statement periods should reject reversed date ranges."""
    with pytest.raises(
        ValueError,
        match="statement period end cannot precede start",
    ):
        StatementPeriod(
            start=date(2026, 2, 1),
            end=date(2026, 1, 31),
        )


def test_position_preserves_security_and_quantity() -> None:
    """Positions should preserve normalized identity and quantity."""
    security = SymbolSecurity("AAPL")

    position = Position(
        security=security,
        quantity=Decimal("12.5"),
    )

    assert position.security is security
    assert position.quantity == Decimal("12.5")


@pytest.mark.parametrize(
    "quantity",
    [
        Decimal("NaN"),
        Decimal("Infinity"),
        Decimal("-Infinity"),
    ],
)
def test_position_rejects_non_finite_quantity(
    quantity: Decimal,
) -> None:
    """Position quantities should be finite."""
    with pytest.raises(
        ValueError,
        match="position quantity must be finite",
    ):
        Position(
            security=SymbolSecurity("AAPL"),
            quantity=quantity,
        )


def test_parsed_statement_preserves_statement_identity() -> None:
    """Parsed statements should preserve their normalized contents."""
    source = StatementSource(
        path=Path("statement.pdf"),
        sha256="abc123",
    )
    period = StatementPeriod(
        start=date(2026, 1, 1),
        end=date(2026, 1, 31),
    )
    position = Position(
        security=SymbolSecurity("AAPL"),
        quantity=Decimal("10"),
    )
    evidence = SourceEvidence(
        source=source,
        page=2,
        section="Account Activity",
        raw_text="Deposit 100.00",
        processor="test.processor",
        sequence=1,
    )
    event = CashTransferEvent(
        date=date(2026, 1, 15),
        transfer_type=CashTransferType.DEPOSIT,
        amount=Decimal("100.00"),
        evidence=evidence,
    )

    statement = ParsedStatement(
        source=source,
        broker=Broker.CHARLES_SCHWAB,
        period=period,
        events=(event,),
        positions=(position,),
    )

    assert statement.source is source
    assert statement.broker is Broker.CHARLES_SCHWAB
    assert statement.period is period
    assert statement.events == (event,)
    assert statement.positions == (position,)
