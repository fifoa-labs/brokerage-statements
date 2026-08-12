"""
src/brokerage_statements/domain/statements.py

Broker-neutral statement-level domain models.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import date
    from decimal import Decimal

    from .events import NormalizedEvent
    from .evidence import StatementSource
    from .securities import Security


class Broker(StrEnum):
    """Supported brokerage institutions."""

    TD_AMERITRADE = "tdameritrade"
    CHARLES_SCHWAB = "charlesschwab"


@dataclass(frozen=True, slots=True)
class StatementPeriod:
    """Inclusive statement reporting period."""

    start: date
    end: date

    def __post_init__(self) -> None:
        """Validate statement period ordering."""
        if self.end < self.start:
            msg = "statement period end cannot precede start."
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class Position:
    """Closing security position reported by a statement."""

    security: Security
    quantity: Decimal

    def __post_init__(self) -> None:
        """Validate position quantity."""
        if not self.quantity.is_finite():
            msg = "position quantity must be finite."
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class ParsedStatement:
    """Normalized representation of one brokerage statement."""

    source: StatementSource
    broker: Broker
    period: StatementPeriod
    events: tuple[NormalizedEvent, ...] = ()
    positions: tuple[Position, ...] = ()
