"""
src/brokerage_statements/domain/events.py

Broker-neutral normalized brokerage event models.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import date as Date  # noqa: N812
    from decimal import Decimal

    from .evidence import SourceEvidence
    from .securities import OptionSecurity, Security


class TradeSide(StrEnum):
    """Supported trade directions."""

    BUY = "buy"
    SELL = "sell"


class TradeStatus(StrEnum):
    """Supported trade settlement states."""

    PENDING = "pending"
    SETTLED = "settled"


class PositionEffect(StrEnum):
    """Supported option position effects."""

    OPEN = "open"
    CLOSE = "close"


class CashTransferType(StrEnum):
    """Supported external cash transfer directions."""

    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"


class IncomeType(StrEnum):
    """Supported brokerage income categories."""

    DIVIDEND = "dividend"
    INTEREST = "interest"
    OTHER = "other"


class SecurityTransferDirection(StrEnum):
    """Supported security transfer directions."""

    IN = "in"
    OUT = "out"


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

    date: Date
    security: Security
    side: TradeSide
    status: TradeStatus
    quantity: Decimal
    price: Decimal
    amount: Decimal
    evidence: tuple[SourceEvidence, ...]
    settlement_date: Date | None = None
    position_effect: PositionEffect | None = None

    def __post_init__(self) -> None:
        """Validate trade values."""
        _require_evidence(self.evidence)
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

    date: Date
    transfer_type: CashTransferType
    amount: Decimal
    evidence: tuple[SourceEvidence, ...]

    def __post_init__(self) -> None:
        """Validate cash transfer values."""
        _require_evidence(self.evidence)
        _require_positive(self.amount, "cash transfer amount")


@dataclass(frozen=True, slots=True)
class IncomeEvent:
    """Normalized brokerage income event."""

    date: Date
    income_type: IncomeType
    amount: Decimal
    evidence: tuple[SourceEvidence, ...]

    def __post_init__(self) -> None:
        """Validate income values."""
        _require_evidence(self.evidence)
        _require_positive(self.amount, "income amount")


@dataclass(frozen=True, slots=True)
class FeeEvent:
    """Normalized brokerage fee."""

    date: Date
    amount: Decimal
    evidence: tuple[SourceEvidence, ...]
    description: str | None = None

    def __post_init__(self) -> None:
        """Validate fee values."""
        _require_evidence(self.evidence)
        _require_positive(self.amount, "fee amount")


@dataclass(frozen=True, slots=True)
class SecurityTransferEvent:
    """Normalized movement of a security into or out of the account."""

    date: Date
    security: Security
    direction: SecurityTransferDirection
    quantity: Decimal
    evidence: tuple[SourceEvidence, ...]

    def __post_init__(self) -> None:
        """Validate security transfer values."""
        _require_evidence(self.evidence)
        _require_positive(
            self.quantity,
            "security transfer quantity",
        )


@dataclass(frozen=True, slots=True)
class CorporateActionEvent:
    """Normalized corporate action affecting securities."""

    date: Date
    action_type: CorporateActionType
    source_security: Security
    evidence: tuple[SourceEvidence, ...]
    target_security: Security | None = None
    quantity_before: Decimal | None = None
    quantity_after: Decimal | None = None
    cash: Decimal | None = None

    def __post_init__(self) -> None:
        """Validate corporate action values."""
        _require_evidence(self.evidence)

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
            _require_non_negative(
                self.cash,
                "corporate action cash",
            )


@dataclass(frozen=True, slots=True)
class OptionExpirationEvent:
    """Normalized expiration of an option contract."""

    date: Date
    security: OptionSecurity
    contracts: Decimal
    evidence: tuple[SourceEvidence, ...]

    def __post_init__(self) -> None:
        """Validate option expiration values."""
        _require_evidence(self.evidence)
        _require_positive(
            self.contracts,
            "option contracts",
        )


NormalizedEvent = (
    TradeEvent
    | CashTransferEvent
    | IncomeEvent
    | FeeEvent
    | SecurityTransferEvent
    | CorporateActionEvent
    | OptionExpirationEvent
)


def _require_evidence(
    evidence: tuple[SourceEvidence, ...],
) -> None:
    """Require at least one source evidence occurrence."""
    if not evidence:
        msg = "event evidence must not be empty."
        raise ValueError(msg)


def _require_finite(
    value: Decimal,
    name: str,
) -> None:
    """Require a finite decimal value."""
    if not value.is_finite():
        msg = f"{name} must be finite."
        raise ValueError(msg)


def _require_positive(
    value: Decimal,
    name: str,
) -> None:
    """Require a finite decimal value greater than zero."""
    _require_finite(value, name)

    if value <= 0:
        msg = f"{name} must be greater than zero."
        raise ValueError(msg)


def _require_non_negative(
    value: Decimal,
    name: str,
) -> None:
    """Require a finite decimal value greater than or equal to zero."""
    _require_finite(value, name)

    if value < 0:
        msg = f"{name} must not be negative."
        raise ValueError(msg)
