"""
tests/text/test_models.py

Tests for normalized brokerage statement text models.
"""

from __future__ import annotations

import pytest

from brokerage_statements.text import StatementPage, StatementText


def test_statement_page_preserves_values() -> None:
    """Statement pages should preserve page number and text."""
    page = StatementPage(
        number=1,
        text="Account Summary",
    )

    assert page.number == 1
    assert page.text == "Account Summary"


@pytest.mark.parametrize(
    "number",
    [
        0,
        -1,
    ],
)
def test_statement_page_rejects_invalid_number(
    number: int,
) -> None:
    """Statement page numbers should be one-based."""
    with pytest.raises(
        ValueError,
        match="page number must be at least 1",
    ):
        StatementPage(
            number=number,
            text="Account Summary",
        )


def test_statement_text_preserves_pages() -> None:
    """Statement text should preserve page ordering."""
    pages = (
        StatementPage(number=1, text="Page one"),
        StatementPage(number=2, text="Page two"),
    )

    statement = StatementText(pages=pages)

    assert statement.pages == pages


def test_statement_text_combines_page_text() -> None:
    """Combined text should preserve statement page order."""
    statement = StatementText(
        pages=(
            StatementPage(number=1, text="Page one"),
            StatementPage(number=2, text="Page two"),
            StatementPage(number=3, text="Page three"),
        ),
    )

    assert statement.text == "Page one\nPage two\nPage three"


def test_statement_text_allows_empty_pages() -> None:
    """Statement text may represent an empty extraction result."""
    statement = StatementText(pages=())

    assert statement.pages == ()
    assert statement.text == ""
