"""
tests/processors/charlesschwab/test_sections.py

Tests for Charles Schwab structural section discovery.
"""

from __future__ import annotations

import pytest

from brokerage_statements.processors.charlesschwab.sections import (
    extract_sections,
)
from brokerage_statements.text import StatementPage, StatementText


def test_extract_sections_preserves_2023_section_ranges() -> None:
    """2023 positions should span through the transaction-summary page."""
    summary = StatementPage(
        number=1,
        text=("Schwab One® Account of\nAccount Summary"),
    )
    positions_summary = StatementPage(
        number=2,
        text=("Schwab One® Account of\nPositions - Summary"),
    )
    positions = StatementPage(
        number=3,
        text=(
            "Positions - Equities\n"
            "Positions - Other Assets\n"
            "Transactions - Summary"
        ),
    )
    details = StatementPage(
        number=4,
        text=(
            "Transaction Details\n"
            "11/29 Interest Credit Interest\n"
            "Terms and Conditions"
        ),
    )

    sections = extract_sections(
        StatementText(
            pages=(
                summary,
                positions_summary,
                positions,
                details,
            ),
        )
    )

    assert sections.summary == (summary,)
    assert sections.positions == (
        positions_summary,
        positions,
    )
    assert sections.transaction_summary == (positions,)
    assert sections.transaction_details == (details,)


def test_extract_sections_preserves_2026_single_position_page() -> None:
    """Later Schwab statements may contain positions on one page."""
    summary = StatementPage(
        number=1,
        text="Account Summary",
    )
    allocation = StatementPage(
        number=2,
        text="Asset Allocation",
    )
    positions = StatementPage(
        number=3,
        text=(
            "Positions - Summary\n"
            "Positions - Other Assets\n"
            "Transactions - Summary"
        ),
    )
    terms = StatementPage(
        number=4,
        text="Terms and Conditions",
    )

    sections = extract_sections(
        StatementText(
            pages=(
                summary,
                allocation,
                positions,
                terms,
            ),
        )
    )

    assert sections.summary == (summary,)
    assert sections.positions == (positions,)
    assert sections.transaction_summary == (positions,)
    assert sections.transaction_details == ()


def test_extract_sections_allows_missing_transaction_details() -> None:
    """Statements without transaction activity may omit detail rows."""
    text = StatementText(
        pages=(
            StatementPage(
                number=1,
                text="Account Summary",
            ),
            StatementPage(
                number=2,
                text=("Positions - Summary\nTransactions - Summary"),
            ),
        ),
    )

    sections = extract_sections(text)

    assert sections.transaction_details == ()


def test_extract_sections_supports_multpage_transaction_details() -> None:
    """Transaction details may span several pages before legal terms."""
    first = StatementPage(
        number=1,
        text="Account Summary",
    )
    positions = StatementPage(
        number=2,
        text=("Positions - Summary\nTransactions - Summary"),
    )
    details = StatementPage(
        number=3,
        text="Transaction Details\nfirst transaction",
    )
    continuation = StatementPage(
        number=4,
        text="continued transaction rows",
    )
    terms = StatementPage(
        number=5,
        text=("final transaction row\nTerms and Conditions"),
    )

    sections = extract_sections(
        StatementText(
            pages=(
                first,
                positions,
                details,
                continuation,
                terms,
            ),
        )
    )

    assert sections.transaction_details == (
        details,
        continuation,
        terms,
    )


def test_extract_sections_allows_details_without_terms_marker() -> None:
    """Detail pages should remain usable if legal terms are absent."""
    summary = StatementPage(
        number=1,
        text="Account Summary",
    )
    positions = StatementPage(
        number=2,
        text=("Positions - Summary\nTransactions - Summary"),
    )
    details = StatementPage(
        number=3,
        text="Transaction Details",
    )
    continuation = StatementPage(
        number=4,
        text="continued transaction rows",
    )

    sections = extract_sections(
        StatementText(
            pages=(
                summary,
                positions,
                details,
                continuation,
            ),
        )
    )

    assert sections.transaction_details == (
        details,
        continuation,
    )


@pytest.mark.parametrize(
    ("missing", "match"),
    [
        (
            "Account Summary",
            "Account Summary section not found",
        ),
        (
            "Positions - Summary",
            "Positions - Summary section not found",
        ),
        (
            "Transactions - Summary",
            "Transactions - Summary section not found",
        ),
    ],
)
def test_extract_sections_rejects_missing_required_section(
    missing: str,
    match: str,
) -> None:
    """Required Schwab monthly sections should fail explicitly."""
    markers = (
        "Account Summary",
        "Positions - Summary",
        "Transactions - Summary",
    )

    pages = tuple(
        StatementPage(
            number=index,
            text=marker,
        )
        for index, marker in enumerate(
            (marker for marker in markers if marker != missing),
            start=1,
        )
    )

    with pytest.raises(
        ValueError,
        match=match,
    ):
        extract_sections(
            StatementText(
                pages=pages,
            )
        )


def test_extract_sections_rejects_invalid_section_order() -> None:
    """Transaction summary must not precede reported positions."""
    text = StatementText(
        pages=(
            StatementPage(
                number=1,
                text="Account Summary",
            ),
            StatementPage(
                number=2,
                text="Transactions - Summary",
            ),
            StatementPage(
                number=3,
                text="Positions - Summary",
            ),
        ),
    )

    with pytest.raises(
        ValueError,
        match=(
            "Transactions - Summary section occurs before Positions - Summary"
        ),
    ):
        extract_sections(text)
