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


def make_source() -> StatementSource:
    """Return reusable statement source identity."""
    return StatementSource(
        path=Path("statement.pdf"),
        sha256="abc123",
    )


def make_evidence() -> SourceEvidence:
    """Return reusable statement evidence."""
    return SourceEvidence(
        source=make_source(),
        page=2,
        section="Positions",
        raw_text="AAPL 10",
        processor="test.processor",
        sequence=1,
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

    period = StatementPeriod(
        start=day,
        end=day,
    )

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


def test_position_preserves_security_quantity_and_evidence() -> None:
    """Positions should preserve normalized source data."""
    security = SymbolSecurity("AAPL")
    evidence = make_evidence()

    position = Position(
        security=security,
        quantity=Decimal("12.5"),
        evidence=evidence,
    )

    assert position.security is security
    assert position.quantity == Decimal("12.5")
    assert position.evidence is evidence


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
            evidence=make_evidence(),
        )


def test_parsed_statement_preserves_statement_identity() -> None:
    """Parsed statements should preserve normalized contents."""
    source = make_source()
    evidence = SourceEvidence(
        source=source,
        page=2,
        section="Account Activity",
        raw_text="Deposit 100.00",
        processor="test.processor",
        sequence=1,
    )
    period = StatementPeriod(
        start=date(2026, 1, 1),
        end=date(2026, 1, 31),
    )
    position = Position(
        security=SymbolSecurity("AAPL"),
        quantity=Decimal("10"),
        evidence=evidence,
    )
    event = CashTransferEvent(
        date=date(2026, 1, 15),
        transfer_type=CashTransferType.DEPOSIT,
        amount=Decimal("100.00"),
        evidence=(evidence,),
    )

    statement = ParsedStatement(
        source=source,
        broker=Broker.CHARLES_SCHWAB,
        processor_name="test.processor",
        account_id="1234",
        currency="USD",
        period=period,
        events=(event,),
        positions=(position,),
    )

    assert statement.source is source
    assert statement.broker is Broker.CHARLES_SCHWAB
    assert statement.processor_name == "test.processor"
    assert statement.account_id == "1234"
    assert statement.currency == "USD"
    assert statement.period is period
    assert statement.events == (event,)
    assert statement.positions == (position,)


def test_parsed_statement_normalizes_identity_text() -> None:
    """Statement identity text should normalize consistently."""
    statement = ParsedStatement(
        source=make_source(),
        broker=Broker.TD_AMERITRADE,
        processor_name="  test.processor  ",
        account_id="  ****1234  ",
        currency=" usd ",
        period=StatementPeriod(
            start=date(2026, 1, 1),
            end=date(2026, 1, 31),
        ),
    )

    assert statement.processor_name == "test.processor"
    assert statement.account_id == "****1234"
    assert statement.currency == "USD"


def test_parsed_statement_rejects_empty_processor_name() -> None:
    """Parsed statements should require processor identity."""
    with pytest.raises(
        ValueError,
        match="processor_name must not be empty",
    ):
        ParsedStatement(
            source=make_source(),
            broker=Broker.CHARLES_SCHWAB,
            processor_name=" ",
            account_id="1234",
            currency="USD",
            period=StatementPeriod(
                start=date(2026, 1, 1),
                end=date(2026, 1, 31),
            ),
        )


def test_parsed_statement_rejects_empty_account_id() -> None:
    """Parsed statements should require account identity."""
    with pytest.raises(
        ValueError,
        match="account_id must not be empty",
    ):
        ParsedStatement(
            source=make_source(),
            broker=Broker.CHARLES_SCHWAB,
            processor_name="test.processor",
            account_id=" ",
            currency="USD",
            period=StatementPeriod(
                start=date(2026, 1, 1),
                end=date(2026, 1, 31),
            ),
        )


def test_parsed_statement_rejects_empty_currency() -> None:
    """Parsed statements should require currency identity."""
    with pytest.raises(
        ValueError,
        match="currency must not be empty",
    ):
        ParsedStatement(
            source=make_source(),
            broker=Broker.CHARLES_SCHWAB,
            processor_name="test.processor",
            account_id="1234",
            currency=" ",
            period=StatementPeriod(
                start=date(2026, 1, 1),
                end=date(2026, 1, 31),
            ),
        )
