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
    StatementParseError,
    StatementSourceError,
    UnknownActivityError,
    UnresolvedSecurityError,
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


def test_statement_parse_error_inheritance() -> None:
    """Statement parsing errors should use the package hierarchy."""
    error = StatementParseError("parse failed")

    assert isinstance(error, BrokerageStatementsError)
    assert str(error) == "parse failed"


def test_unknown_activity_error_inheritance() -> None:
    """Unknown activity should be a statement parsing error."""
    error = UnknownActivityError("unknown activity")

    assert isinstance(error, StatementParseError)
    assert isinstance(error, BrokerageStatementsError)
    assert str(error) == "unknown activity"


def test_invalid_processor_result_error_inheritance() -> None:
    """Invalid processor results should use the package hierarchy."""
    error = InvalidProcessorResultError("invalid processor result")

    assert isinstance(error, BrokerageStatementsError)
    assert str(error) == "invalid processor result"


def test_unresolved_security_error_inheritance() -> None:
    """Unresolved securities should be statement parsing errors."""
    error = UnresolvedSecurityError("unresolved security")

    assert isinstance(error, StatementParseError)
    assert isinstance(error, BrokerageStatementsError)
    assert str(error) == "unresolved security"
