"""
src/brokerage_statements/domain/__init__.py

Broker-neutral domain primitives for normalized brokerage statements.
"""

from __future__ import annotations

from .amounts import to_decimal
from .events import (
    CashTransferEvent,
    CashTransferType,
    CorporateActionEvent,
    CorporateActionType,
    FeeEvent,
    IncomeEvent,
    IncomeType,
    NormalizedEvent,
    OptionExpirationEvent,
    SecurityTransferEvent,
    TradeEvent,
    TradeSide,
)
from .evidence import SourceEvidence, StatementSource
from .securities import (
    OptionRight,
    OptionSecurity,
    Security,
    SymbolSecurity,
)
from .statements import (
    Broker,
    ParsedStatement,
    Position,
    StatementPeriod,
)

__all__ = [
    "Broker",
    "CashTransferEvent",
    "CashTransferType",
    "CorporateActionEvent",
    "CorporateActionType",
    "FeeEvent",
    "IncomeEvent",
    "IncomeType",
    "NormalizedEvent",
    "OptionExpirationEvent",
    "OptionRight",
    "OptionSecurity",
    "ParsedStatement",
    "Position",
    "Security",
    "SecurityTransferEvent",
    "SourceEvidence",
    "StatementPeriod",
    "StatementSource",
    "SymbolSecurity",
    "TradeEvent",
    "TradeSide",
    "to_decimal",
]
