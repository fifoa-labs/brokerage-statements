"""
tests/processors/charlesschwab/test_identity.py

Tests for Charles Schwab statement identity extraction.
"""

from __future__ import annotations

from datetime import date

import pytest

from brokerage_statements.processors.charlesschwab.identity import (
    parse_statement_identity,
)
from brokerage_statements.text import StatementPage, StatementText


def make_text(
    first_page: str,
    *additional_pages: str,
) -> StatementText:
    """Return statement text containing supplied page contents."""
    pages = (first_page, *additional_pages)

    return StatementText(
        pages=tuple(
            StatementPage(
                number=number,
                text=value,
            )
            for number, value in enumerate(
                pages,
                start=1,
            )
        ),
    )


@pytest.mark.parametrize(
    ("period_text", "start", "end"),
    [
        (
            "November1-30,2023",
            date(2023, 11, 1),
            date(2023, 11, 30),
        ),
        (
            "May 1-31, 2026",
            date(2026, 5, 1),
            date(2026, 5, 31),
        ),
    ],
)
def test_parse_statement_identity_preserves_values(
    period_text: str,
    start: date,
    end: date,
) -> None:
    """Statement identity should preserve account and period."""
    text = make_text(
        "Schwab One® Account of\n"
        "AccountNumber StatementPeriod\n"
        f"ACCOUNTOWNER 1234-5678 {period_text}"
    )

    identity = parse_statement_identity(text)

    assert identity.account_id == "1234-5678"
    assert identity.start == start
    assert identity.end == end


def test_parse_statement_identity_uses_full_first_page_account() -> None:
    """Identity should use the full account number from page one."""
    text = make_text(
        "Schwab One® Account of\n"
        "AccountNumber StatementPeriod\n"
        "ACCOUNTOWNER 1234-5678 June1-30,2026",
        "Schwab One® Account of\n"
        "AccountNumber StatementPeriod\n"
        "ACCOUNTOWNER ****-*5678 June1-30,2026",
    )

    identity = parse_statement_identity(text)

    assert identity.account_id == "1234-5678"


def test_parse_statement_identity_rejects_missing_account() -> None:
    """Statement identity should require a full account number."""
    text = make_text(
        "Schwab One® Account of\n"
        "StatementPeriod\n"
        "ACCOUNTOWNER November1-30,2023"
    )

    with pytest.raises(
        ValueError,
        match="Charles Schwab account number not found",
    ):
        parse_statement_identity(text)


def test_parse_statement_identity_rejects_missing_period() -> None:
    """Statement identity should require a statement period."""
    text = make_text(
        "Schwab One® Account of\nAccountNumber\nACCOUNTOWNER 1234-5678"
    )

    with pytest.raises(
        ValueError,
        match="Charles Schwab statement period not found",
    ):
        parse_statement_identity(text)
