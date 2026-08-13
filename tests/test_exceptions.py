"""
tests/test_exceptions.py

Tests for the brokerage-statements exception hierarchy.
"""

from __future__ import annotations

from brokerage_statements.exceptions import (
    AmbiguousBrokerError,
    AmbiguousProcessorError,
    BrokerageStatementsError,
    BrokerDetectionError,
    InvalidDecimalError,
    InvalidProcessorResultError,
    ProcessorSelectionError,
    StatementSourceError,
    UnsupportedBrokerError,
    UnsupportedStatementError,
)


def test_brokerage_statements_error_message() -> None:
    """The package base error should preserve its message."""
    error = BrokerageStatementsError("test error")

    assert str(error) == "test error"


def test_invalid_decimal_error_inheritance() -> None:
    """Invalid decimal errors should use the package hierarchy."""
    error = InvalidDecimalError("invalid decimal")

    assert isinstance(error, BrokerageStatementsError)
    assert isinstance(error, ValueError)
    assert str(error) == "invalid decimal"


def test_broker_detection_error_inheritance() -> None:
    """Broker detection errors should use the package hierarchy."""
    error = BrokerDetectionError("detection failed")

    assert isinstance(error, BrokerageStatementsError)
    assert str(error) == "detection failed"


def test_unsupported_broker_error_inheritance() -> None:
    """Unsupported brokers should be broker detection errors."""
    error = UnsupportedBrokerError("unsupported broker")

    assert isinstance(error, BrokerDetectionError)
    assert isinstance(error, BrokerageStatementsError)
    assert str(error) == "unsupported broker"


def test_ambiguous_broker_error_inheritance() -> None:
    """Ambiguous brokers should be broker detection errors."""
    error = AmbiguousBrokerError("ambiguous broker")

    assert isinstance(error, BrokerDetectionError)
    assert isinstance(error, BrokerageStatementsError)
    assert str(error) == "ambiguous broker"


def test_processor_selection_error_inheritance() -> None:
    """Processor selection errors should use the package hierarchy."""
    error = ProcessorSelectionError("selection failed")

    assert isinstance(error, BrokerageStatementsError)
    assert str(error) == "selection failed"


def test_unsupported_statement_error_inheritance() -> None:
    """Unsupported statements should be processor selection errors."""
    error = UnsupportedStatementError("unsupported statement")

    assert isinstance(error, ProcessorSelectionError)
    assert isinstance(error, BrokerageStatementsError)
    assert str(error) == "unsupported statement"


def test_ambiguous_processor_error_inheritance() -> None:
    """Ambiguous processors should be processor selection errors."""
    error = AmbiguousProcessorError("ambiguous processor")

    assert isinstance(error, ProcessorSelectionError)
    assert isinstance(error, BrokerageStatementsError)
    assert str(error) == "ambiguous processor"


def test_statement_source_error_inheritance() -> None:
    """Statement source errors should use the package hierarchy."""
    error = StatementSourceError("source failed")

    assert isinstance(error, BrokerageStatementsError)
    assert str(error) == "source failed"


def test_invalid_processor_result_error_inheritance() -> None:
    """Invalid processor results should use the package hierarchy."""
    error = InvalidProcessorResultError("invalid processor result")

    assert isinstance(error, BrokerageStatementsError)
    assert str(error) == "invalid processor result"
