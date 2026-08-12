"""
tests/domain/test_events.py

Tests for broker-neutral normalized brokerage event models.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from brokerage_statements.domain import (
    CashTransferEvent,
    CashTransferType,
    CorporateActionEvent,
    CorporateActionType,
    FeeEvent,
    IncomeEvent,
    IncomeType,
    OptionExpirationEvent,
    OptionRight,
    OptionSecurity,
    PositionEffect,
    SecurityTransferDirection,
    SecurityTransferEvent,
    SourceEvidence,
    StatementSource,
    SymbolSecurity,
    TradeEvent,
    TradeSide,
    TradeStatus,
)


@pytest.fixture
def evidence() -> SourceEvidence:
    """Return reusable source evidence for event tests."""
    source = StatementSource(
        path=Path("statement.pdf"),
        sha256="abc123",
    )

    return SourceEvidence(
        source=source,
        page=1,
        section="Account Activity",
        raw_text="fixture row",
        processor="test.processor",
        sequence=1,
    )


def test_trade_event_preserves_values(
    evidence: SourceEvidence,
) -> None:
    """Trade events should preserve normalized trade values."""
    security = SymbolSecurity("AAPL")

    event = TradeEvent(
        date=date(2026, 1, 15),
        security=security,
        side=TradeSide.BUY,
        status=TradeStatus.SETTLED,
        quantity=Decimal("10"),
        price=Decimal("200.50"),
        amount=Decimal("2005.00"),
        evidence=(evidence,),
        settlement_date=date(2026, 1, 17),
        position_effect=PositionEffect.OPEN,
    )

    assert event.date == date(2026, 1, 15)
    assert event.security is security
    assert event.side is TradeSide.BUY
    assert event.status is TradeStatus.SETTLED
    assert event.quantity == Decimal("10")
    assert event.price == Decimal("200.50")
    assert event.amount == Decimal("2005.00")
    assert event.evidence == (evidence,)
    assert event.settlement_date == date(2026, 1, 17)
    assert event.position_effect is PositionEffect.OPEN


def test_trade_event_allows_optional_trade_metadata(
    evidence: SourceEvidence,
) -> None:
    """Trade metadata may omit settlement and position effect."""
    event = TradeEvent(
        date=date(2026, 1, 15),
        security=SymbolSecurity("AAPL"),
        side=TradeSide.SELL,
        status=TradeStatus.PENDING,
        quantity=Decimal("1"),
        price=Decimal("10"),
        amount=Decimal("10"),
        evidence=(evidence,),
    )

    assert event.status is TradeStatus.PENDING
    assert event.settlement_date is None
    assert event.position_effect is None


@pytest.mark.parametrize(
    "quantity",
    [
        Decimal("0"),
        Decimal("-1"),
    ],
)
def test_trade_event_rejects_non_positive_quantity(
    evidence: SourceEvidence,
    quantity: Decimal,
) -> None:
    """Trade quantities should be greater than zero."""
    with pytest.raises(
        ValueError,
        match="trade quantity must be greater than zero",
    ):
        TradeEvent(
            date=date(2026, 1, 15),
            security=SymbolSecurity("AAPL"),
            side=TradeSide.BUY,
            status=TradeStatus.SETTLED,
            quantity=quantity,
            price=Decimal("10"),
            amount=Decimal("10"),
            evidence=(evidence,),
        )


@pytest.mark.parametrize(
    ("field", "value", "match"),
    [
        (
            "quantity",
            Decimal("NaN"),
            "quantity must be finite",
        ),
        (
            "price",
            Decimal("Infinity"),
            "price must be finite",
        ),
        (
            "amount",
            Decimal("-Infinity"),
            "amount must be finite",
        ),
    ],
)
def test_trade_event_rejects_non_finite_values(
    evidence: SourceEvidence,
    field: str,
    value: Decimal,
    match: str,
) -> None:
    """Trade decimal fields should be finite."""
    values = {
        "quantity": Decimal("10"),
        "price": Decimal("5"),
        "amount": Decimal("50"),
    }
    values[field] = value

    with pytest.raises(ValueError, match=match):
        TradeEvent(
            date=date(2026, 1, 15),
            security=SymbolSecurity("AAPL"),
            side=TradeSide.SELL,
            status=TradeStatus.SETTLED,
            quantity=values["quantity"],
            price=values["price"],
            amount=values["amount"],
            evidence=(evidence,),
        )


def test_trade_event_rejects_negative_price(
    evidence: SourceEvidence,
) -> None:
    """Trade prices should not be negative."""
    with pytest.raises(
        ValueError,
        match="trade price must not be negative",
    ):
        TradeEvent(
            date=date(2026, 1, 15),
            security=SymbolSecurity("AAPL"),
            side=TradeSide.BUY,
            status=TradeStatus.SETTLED,
            quantity=Decimal("1"),
            price=Decimal("-1"),
            amount=Decimal("1"),
            evidence=(evidence,),
        )


def test_cash_transfer_event_preserves_values(
    evidence: SourceEvidence,
) -> None:
    """Cash transfer events should preserve normalized values."""
    event = CashTransferEvent(
        date=date(2026, 1, 10),
        transfer_type=CashTransferType.DEPOSIT,
        amount=Decimal("1000"),
        evidence=(evidence,),
    )

    assert event.transfer_type is CashTransferType.DEPOSIT
    assert event.amount == Decimal("1000")
    assert event.evidence == (evidence,)


@pytest.mark.parametrize(
    "amount",
    [
        Decimal("0"),
        Decimal("-1"),
    ],
)
def test_cash_transfer_event_rejects_non_positive_amount(
    evidence: SourceEvidence,
    amount: Decimal,
) -> None:
    """Cash transfer amounts should be greater than zero."""
    with pytest.raises(
        ValueError,
        match="cash transfer amount must be greater than zero",
    ):
        CashTransferEvent(
            date=date(2026, 1, 10),
            transfer_type=CashTransferType.WITHDRAWAL,
            amount=amount,
            evidence=(evidence,),
        )


def test_cash_transfer_event_rejects_non_finite_amount(
    evidence: SourceEvidence,
) -> None:
    """Cash transfer amounts should be finite."""
    with pytest.raises(
        ValueError,
        match="cash transfer amount must be finite",
    ):
        CashTransferEvent(
            date=date(2026, 1, 10),
            transfer_type=CashTransferType.DEPOSIT,
            amount=Decimal("NaN"),
            evidence=(evidence,),
        )


def test_income_event_preserves_values(
    evidence: SourceEvidence,
) -> None:
    """Income events should preserve normalized values."""
    event = IncomeEvent(
        date=date(2026, 1, 10),
        income_type=IncomeType.INTEREST,
        amount=Decimal("12.34"),
        evidence=(evidence,),
    )

    assert event.income_type is IncomeType.INTEREST
    assert event.amount == Decimal("12.34")
    assert event.evidence == (evidence,)


@pytest.mark.parametrize(
    "amount",
    [
        Decimal("0"),
        Decimal("-1"),
    ],
)
def test_income_event_rejects_non_positive_amount(
    evidence: SourceEvidence,
    amount: Decimal,
) -> None:
    """Income amounts should be greater than zero."""
    with pytest.raises(
        ValueError,
        match="income amount must be greater than zero",
    ):
        IncomeEvent(
            date=date(2026, 1, 10),
            income_type=IncomeType.DIVIDEND,
            amount=amount,
            evidence=(evidence,),
        )


def test_income_event_rejects_non_finite_amount(
    evidence: SourceEvidence,
) -> None:
    """Income amounts should be finite."""
    with pytest.raises(
        ValueError,
        match="income amount must be finite",
    ):
        IncomeEvent(
            date=date(2026, 1, 10),
            income_type=IncomeType.OTHER,
            amount=Decimal("Infinity"),
            evidence=(evidence,),
        )


def test_fee_event_preserves_values(
    evidence: SourceEvidence,
) -> None:
    """Fee events should preserve amount and description."""
    event = FeeEvent(
        date=date(2026, 1, 10),
        amount=Decimal("38"),
        evidence=(evidence,),
        description="Mandatory reorganization fee",
    )

    assert event.amount == Decimal("38")
    assert event.description == "Mandatory reorganization fee"
    assert event.evidence == (evidence,)


@pytest.mark.parametrize(
    "amount",
    [
        Decimal("0"),
        Decimal("-1"),
    ],
)
def test_fee_event_rejects_non_positive_amount(
    evidence: SourceEvidence,
    amount: Decimal,
) -> None:
    """Fee amounts should be greater than zero."""
    with pytest.raises(
        ValueError,
        match="fee amount must be greater than zero",
    ):
        FeeEvent(
            date=date(2026, 1, 10),
            amount=amount,
            evidence=(evidence,),
        )


def test_fee_event_rejects_non_finite_amount(
    evidence: SourceEvidence,
) -> None:
    """Fee amounts should be finite."""
    with pytest.raises(
        ValueError,
        match="fee amount must be finite",
    ):
        FeeEvent(
            date=date(2026, 1, 10),
            amount=Decimal("NaN"),
            evidence=(evidence,),
        )


@pytest.mark.parametrize(
    "direction",
    [
        SecurityTransferDirection.IN,
        SecurityTransferDirection.OUT,
    ],
)
def test_security_transfer_event_preserves_direction(
    evidence: SourceEvidence,
    direction: SecurityTransferDirection,
) -> None:
    """Security transfers should preserve explicit direction."""
    event = SecurityTransferEvent(
        date=date(2026, 1, 10),
        security=SymbolSecurity("AAPL"),
        direction=direction,
        quantity=Decimal("10"),
        evidence=(evidence,),
    )

    assert event.direction is direction
    assert event.quantity == Decimal("10")
    assert event.evidence == (evidence,)


@pytest.mark.parametrize(
    "quantity",
    [
        Decimal("0"),
        Decimal("-10"),
    ],
)
def test_security_transfer_event_rejects_non_positive_quantity(
    evidence: SourceEvidence,
    quantity: Decimal,
) -> None:
    """Security transfer quantities should be positive."""
    with pytest.raises(
        ValueError,
        match="security transfer quantity must be greater than zero",
    ):
        SecurityTransferEvent(
            date=date(2026, 1, 10),
            security=SymbolSecurity("AAPL"),
            direction=SecurityTransferDirection.IN,
            quantity=quantity,
            evidence=(evidence,),
        )


def test_security_transfer_event_rejects_non_finite_quantity(
    evidence: SourceEvidence,
) -> None:
    """Security transfer quantities should be finite."""
    with pytest.raises(
        ValueError,
        match="security transfer quantity must be finite",
    ):
        SecurityTransferEvent(
            date=date(2026, 1, 10),
            security=SymbolSecurity("AAPL"),
            direction=SecurityTransferDirection.OUT,
            quantity=Decimal("Infinity"),
            evidence=(evidence,),
        )


def test_corporate_action_event_allows_optional_values(
    evidence: SourceEvidence,
) -> None:
    """Corporate actions may omit target, quantities, and cash."""
    event = CorporateActionEvent(
        date=date(2026, 1, 10),
        action_type=CorporateActionType.REVERSE_SPLIT,
        source_security=SymbolSecurity("UAVS"),
        evidence=(evidence,),
    )

    assert event.source_security == SymbolSecurity("UAVS")
    assert event.target_security is None
    assert event.quantity_before is None
    assert event.quantity_after is None
    assert event.cash is None


def test_corporate_action_event_preserves_security_transition(
    evidence: SourceEvidence,
) -> None:
    """Corporate actions should preserve source and target identity."""
    event = CorporateActionEvent(
        date=date(2026, 1, 10),
        action_type=CorporateActionType.SYMBOL_CHANGE,
        source_security=SymbolSecurity("DWACW"),
        target_security=SymbolSecurity("DJTWW"),
        evidence=(evidence,),
    )

    assert event.source_security == SymbolSecurity("DWACW")
    assert event.target_security == SymbolSecurity("DJTWW")


def test_corporate_action_event_preserves_values(
    evidence: SourceEvidence,
) -> None:
    """Corporate actions should preserve supplied economic values."""
    event = CorporateActionEvent(
        date=date(2026, 1, 10),
        action_type=CorporateActionType.REVERSE_SPLIT,
        source_security=SymbolSecurity("UAVS"),
        evidence=(evidence,),
        quantity_before=Decimal("5"),
        quantity_after=Decimal("0.1"),
        cash=Decimal("0.24"),
    )

    assert event.action_type is CorporateActionType.REVERSE_SPLIT
    assert event.quantity_before == Decimal("5")
    assert event.quantity_after == Decimal("0.1")
    assert event.cash == Decimal("0.24")


def test_corporate_action_preserves_multiple_evidence_rows(
    evidence: SourceEvidence,
) -> None:
    """One economic action may retain multiple source rows."""
    second = SourceEvidence(
        source=evidence.source,
        page=2,
        section="Account Activity",
        raw_text="Received replacement security",
        processor="test.processor",
        sequence=2,
    )

    event = CorporateActionEvent(
        date=date(2026, 1, 10),
        action_type=CorporateActionType.SYMBOL_CHANGE,
        source_security=SymbolSecurity("DWACW"),
        target_security=SymbolSecurity("DJTWW"),
        evidence=(evidence, second),
    )

    assert event.evidence == (evidence, second)


@pytest.mark.parametrize(
    ("field", "match"),
    [
        (
            "quantity_before",
            "corporate action quantity_before must be finite",
        ),
        (
            "quantity_after",
            "corporate action quantity_after must be finite",
        ),
        (
            "cash",
            "corporate action cash must be finite",
        ),
    ],
)
def test_corporate_action_event_rejects_non_finite_values(
    evidence: SourceEvidence,
    field: str,
    match: str,
) -> None:
    """Corporate action decimal values should be finite."""
    values: dict[str, Decimal | None] = {
        "quantity_before": Decimal("5"),
        "quantity_after": Decimal("1"),
        "cash": Decimal("0"),
    }
    values[field] = Decimal("NaN")

    with pytest.raises(ValueError, match=match):
        CorporateActionEvent(
            date=date(2026, 1, 10),
            action_type=CorporateActionType.REVERSE_SPLIT,
            source_security=SymbolSecurity("UAVS"),
            evidence=(evidence,),
            quantity_before=values["quantity_before"],
            quantity_after=values["quantity_after"],
            cash=values["cash"],
        )


def test_corporate_action_event_rejects_negative_cash(
    evidence: SourceEvidence,
) -> None:
    """Corporate action cash should not be negative."""
    with pytest.raises(
        ValueError,
        match="corporate action cash must not be negative",
    ):
        CorporateActionEvent(
            date=date(2026, 1, 10),
            action_type=CorporateActionType.CASH_IN_LIEU,
            source_security=SymbolSecurity("UAVS"),
            evidence=(evidence,),
            cash=Decimal("-0.24"),
        )


def test_corporate_action_event_allows_zero_cash(
    evidence: SourceEvidence,
) -> None:
    """Corporate actions may legitimately report zero cash."""
    event = CorporateActionEvent(
        date=date(2026, 1, 10),
        action_type=CorporateActionType.WORTHLESS_SECURITY,
        source_security=SymbolSecurity("PHMB"),
        evidence=(evidence,),
        cash=Decimal("0"),
    )

    assert event.cash == Decimal("0")


def test_option_expiration_event_preserves_values(
    evidence: SourceEvidence,
) -> None:
    """Option expiration events should preserve contract identity."""
    security = OptionSecurity(
        underlying="UVXY",
        expiration=date(2020, 9, 18),
        right=OptionRight.CALL,
        strike=Decimal("30"),
    )

    event = OptionExpirationEvent(
        date=date(2020, 9, 18),
        security=security,
        contracts=Decimal("20"),
        evidence=(evidence,),
    )

    assert event.security is security
    assert event.contracts == Decimal("20")
    assert event.evidence == (evidence,)


@pytest.mark.parametrize(
    "contracts",
    [
        Decimal("0"),
        Decimal("-1"),
    ],
)
def test_option_expiration_event_rejects_non_positive_contracts(
    evidence: SourceEvidence,
    contracts: Decimal,
) -> None:
    """Expired contract quantities should be greater than zero."""
    security = OptionSecurity(
        underlying="UVXY",
        expiration=date(2020, 9, 18),
        right=OptionRight.CALL,
        strike=Decimal("30"),
    )

    with pytest.raises(
        ValueError,
        match="option contracts must be greater than zero",
    ):
        OptionExpirationEvent(
            date=date(2020, 9, 18),
            security=security,
            contracts=contracts,
            evidence=(evidence,),
        )


def test_option_expiration_event_rejects_non_finite_contracts(
    evidence: SourceEvidence,
) -> None:
    """Expired contract quantities should be finite."""
    security = OptionSecurity(
        underlying="UVXY",
        expiration=date(2020, 9, 18),
        right=OptionRight.CALL,
        strike=Decimal("30"),
    )

    with pytest.raises(
        ValueError,
        match="option contracts must be finite",
    ):
        OptionExpirationEvent(
            date=date(2020, 9, 18),
            security=security,
            contracts=Decimal("Infinity"),
            evidence=(evidence,),
        )


def test_event_rejects_empty_evidence() -> None:
    """Normalized events should require source evidence."""
    with pytest.raises(
        ValueError,
        match="event evidence must not be empty",
    ):
        TradeEvent(
            date=date(2026, 1, 15),
            security=SymbolSecurity("AAPL"),
            side=TradeSide.BUY,
            status=TradeStatus.SETTLED,
            quantity=Decimal("1"),
            price=Decimal("10"),
            amount=Decimal("10"),
            evidence=(),
        )
