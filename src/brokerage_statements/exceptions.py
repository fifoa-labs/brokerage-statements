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
