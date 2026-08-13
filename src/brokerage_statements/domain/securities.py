"""
src/brokerage_statements/domain/securities.py

Broker-neutral security identity models.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, TypeAlias

if TYPE_CHECKING:
    from datetime import date
    from decimal import Decimal


class OptionRight(StrEnum):
    """Supported option contract rights."""

    CALL = "call"
    PUT = "put"


@dataclass(frozen=True, slots=True)
class SymbolSecurity:
    """Identify a security represented by a market symbol."""

    symbol: str

    def __post_init__(self) -> None:
        """Validate and normalize the security symbol."""
        normalized = self.symbol.strip().upper()

        if not normalized:
            msg = "symbol must not be empty."
            raise ValueError(msg)

        object.__setattr__(self, "symbol", normalized)


@dataclass(frozen=True, slots=True)
class OptionSecurity:
    """Identify an option contract."""

    underlying: str
    expiration: date
    right: OptionRight
    strike: Decimal

    def __post_init__(self) -> None:
        """Validate and normalize option identity."""
        underlying = self.underlying.strip().upper()

        if not underlying:
            msg = "underlying must not be empty."
            raise ValueError(msg)

        if not self.strike.is_finite():
            msg = "strike must be finite."
            raise ValueError(msg)

        if self.strike <= 0:
            msg = "strike must be greater than zero."
            raise ValueError(msg)

        object.__setattr__(self, "underlying", underlying)


Security: TypeAlias = SymbolSecurity | OptionSecurity
