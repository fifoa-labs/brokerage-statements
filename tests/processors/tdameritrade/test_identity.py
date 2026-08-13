"""
tests/processors/tdameritrade/test_identity.py

Tests for TD Ameritrade statement identity extraction.
"""

from __future__ import annotations

from datetime import date

import pytest

from brokerage_statements.domain import Security, SymbolSecurity
from brokerage_statements.processors.tdameritrade.identity import (
    parse_statement_identity,
)
from brokerage_statements.text import StatementPage, StatementText


def symbol_of(security: Security) -> str:
    """Return the symbol for a symbol-backed security."""
    assert isinstance(security, SymbolSecurity)
    return security.symbol


def make_text(value: str) -> StatementText:
    """Return one-page statement text."""
    return StatementText(
        pages=(
            StatementPage(
                number=1,
                text=value,
            ),
        ),
    )


def test_parse_statement_identity_preserves_values() -> None:
    """Statement identity should preserve account and period."""
    text = make_text(
        "Statement Reporting Period:\n03/01/20 - 03/31/20\nStatement for Account # 498-119578"  # noqa: E501
    )

    identity = parse_statement_identity(text)

    assert identity.account_id == "498-119578"
    assert identity.start == date(2020, 3, 1)
    assert identity.end == date(2020, 3, 31)


def test_parse_statement_identity_rejects_missing_account() -> None:
    """Statement identity should require an account number."""
    text = make_text("Statement Reporting Period:\n03/01/20 - 03/31/20")

    with pytest.raises(
        ValueError,
        match="TD Ameritrade account number not found",
    ):
        parse_statement_identity(text)


def test_parse_statement_identity_rejects_missing_period() -> None:
    """Statement identity should require a reporting period."""
    text = make_text(
        "Statement for Account # 498-119578",
    )

    with pytest.raises(
        ValueError,
        match="TD Ameritrade statement reporting period not found",
    ):
        parse_statement_identity(text)
