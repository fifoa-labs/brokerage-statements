"""
src/brokerage_statements/domain/events.py

Broker-neutral normalized brokerage event models.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import date
    from decimal import Decimal

    from .evidence import SourceEvidence
    from .securities import OptionSecurity, Security


class TradeSide(StrEnum):
    """Supported trade directions."""

    BUY = "buy"
    SELL = "sell"


class CashTransferType(StrEnum):
    """Supported external cash transfer directions."""

    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"


class IncomeType(StrEnum):
    """Supported brokerage income categories."""

    DIVIDEND = "dividend"
    INTEREST = "interest"
    OTHER = "other"


class CorporateActionType(StrEnum):
    """Supported corporate action categories."""

    SPLIT = "split"
    REVERSE_SPLIT = "reverse_split"
    SYMBOL_CHANGE = "symbol_change"
    CONVERSION = "conversion"
    MERGER = "merger"
    ACQUISITION = "acquisition"
    SPINOFF = "spinoff"
    CASH_IN_LIEU = "cash_in_lieu"
    REORGANIZATION = "reorganization"
    BANKRUPTCY = "bankruptcy"
    WORTHLESS_SECURITY = "worthless_security"


@dataclass(frozen=True, slots=True)
class TradeEvent:
    """Normalized brokerage trade."""

    date: date
    security: Security
    side: TradeSide
    quantity: Decimal
    price: Decimal
    amount: Decimal
    evidence: SourceEvidence

    def __post_init__(self) -> None:
        """Validate trade values."""
        _require_finite(self.quantity, "quantity")
        _require_finite(self.price, "price")
        _require_finite(self.amount, "amount")

        if self.quantity <= 0:
            msg = "trade quantity must be greater than zero."
            raise ValueError(msg)

        if self.price < 0:
            msg = "trade price must not be negative."
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class CashTransferEvent:
    """Normalized external cash transfer."""

    date: date
    transfer_type: CashTransferType
    amount: Decimal
    evidence: SourceEvidence

    def __post_init__(self) -> None:
        """Validate cash transfer amount."""
        _require_positive(self.amount, "cash transfer amount")


@dataclass(frozen=True, slots=True)
class IncomeEvent:
    """Normalized brokerage income event."""

    date: date
    income_type: IncomeType
    amount: Decimal
    evidence: SourceEvidence

    def __post_init__(self) -> None:
        """Validate income amount."""
        _require_positive(self.amount, "income amount")


@dataclass(frozen=True, slots=True)
class FeeEvent:
    """Normalized brokerage fee."""

    date: date
    amount: Decimal
    evidence: SourceEvidence
    description: str | None = None

    def __post_init__(self) -> None:
        """Validate fee amount."""
        _require_positive(self.amount, "fee amount")


@dataclass(frozen=True, slots=True)
class SecurityTransferEvent:
    """Normalized movement of a security into or out of the account."""

    date: date
    security: Security
    quantity: Decimal
    evidence: SourceEvidence

    def __post_init__(self) -> None:
        """Validate transferred quantity."""
        _require_finite(self.quantity, "security transfer quantity")

        if self.quantity == 0:
            msg = "security transfer quantity must not be zero."
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class CorporateActionEvent:
    """Normalized corporate action affecting a security."""

    date: date
    action_type: CorporateActionType
    security: Security
    evidence: SourceEvidence
    quantity_before: Decimal | None = None
    quantity_after: Decimal | None = None
    cash: Decimal | None = None

    def __post_init__(self) -> None:
        """Validate optional corporate action values."""
        if self.quantity_before is not None:
            _require_finite(
                self.quantity_before,
                "corporate action quantity_before",
            )

        if self.quantity_after is not None:
            _require_finite(
                self.quantity_after,
                "corporate action quantity_after",
            )

        if self.cash is not None:
            _require_finite(
                self.cash,
                "corporate action cash",
            )


@dataclass(frozen=True, slots=True)
class OptionExpirationEvent:
    """Normalized expiration of an option contract."""

    date: date
    security: OptionSecurity
    contracts: Decimal
    evidence: SourceEvidence

    def __post_init__(self) -> None:
        """Validate expired contract quantity."""
        _require_positive(self.contracts, "option contracts")


NormalizedEvent = (
    TradeEvent
    | CashTransferEvent
    | IncomeEvent
    | FeeEvent
    | SecurityTransferEvent
    | CorporateActionEvent
    | OptionExpirationEvent
)


def _require_finite(value: Decimal, name: str) -> None:
    """Require a finite decimal value."""
    if not value.is_finite():
        msg = f"{name} must be finite."
        raise ValueError(msg)


def _require_positive(value: Decimal, name: str) -> None:
    """Require a finite decimal value greater than zero."""
    _require_finite(value, name)

    if value <= 0:
        msg = f"{name} must be greater than zero."
        raise ValueError(msg)
