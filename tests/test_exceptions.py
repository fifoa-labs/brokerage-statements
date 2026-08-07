"""
tests/test_exceptions.py

Tests for the brokerage-statements exception hierarchy.
"""

from __future__ import annotations

from brokerage_statements.exceptions import BrokerageStatementsError


def test_brokerage_statements_error_message() -> None:
    """The package base error should preserve its message."""
    error = BrokerageStatementsError("test error")

    assert str(error) == "test error"
