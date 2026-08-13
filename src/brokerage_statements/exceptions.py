"""
src/brokerage_statements/exceptions.py

Package-specific exception hierarchy for brokerage statement processing.
"""

from __future__ import annotations


class BrokerageStatementsError(Exception):
    """Base exception for brokerage-statements."""


class InvalidDecimalError(BrokerageStatementsError, ValueError):
    """Raised when a value cannot represent an exact finite decimal."""


class ProcessorSelectionError(BrokerageStatementsError):
    """Base error for processor selection failures."""


class UnsupportedStatementError(ProcessorSelectionError):
    """Raised when no registered processor supports a statement."""


class AmbiguousProcessorError(ProcessorSelectionError):
    """Raised when processor selection has no unique winner."""


class StatementSourceError(BrokerageStatementsError):
    """Raised when a statement source cannot be read."""


class InvalidProcessorResultError(BrokerageStatementsError):
    """Raised when a processor returns inconsistent statement data."""


class BrokerDetectionError(BrokerageStatementsError):
    """Base error for brokerage institution detection failures."""


class UnsupportedBrokerError(BrokerDetectionError):
    """Raised when no supported broker can be detected."""


class AmbiguousBrokerError(BrokerDetectionError):
    """Raised when more than one brokerage institution is detected."""


class StatementParseError(BrokerageStatementsError):
    """Base error for deterministic statement parsing failures."""


class UnknownActivityError(StatementParseError):
    """Raised when statement activity cannot be normalized safely."""
