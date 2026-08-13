"""
tests/processors/tdameritrade/test_sections.py

Tests for TD Ameritrade structural section discovery.
"""

from __future__ import annotations

import pytest

from brokerage_statements.processors.tdameritrade.sections import (
    extract_sections,
)
from brokerage_statements.text import StatementPage, StatementText


def test_extract_sections_preserves_matching_pages() -> None:
    """Known statement sections should retain their source pages."""
    summary = StatementPage(
        number=3,
        text="Portfolio Summary",
    )
    positions = StatementPage(
        number=4,
        text="Account Positions",
    )
    activity = StatementPage(
        number=5,
        text="Account Activity",
    )
    pending = StatementPage(
        number=9,
        text="Trades Pending Settlement",
    )

    sections = extract_sections(
        StatementText(
            pages=(
                summary,
                positions,
                activity,
                pending,
            ),
        )
    )

    assert sections.summary == (summary,)
    assert sections.positions == (positions,)
    assert sections.activity == (activity,)
    assert sections.pending == (pending,)


def test_extract_sections_allows_missing_pending_section() -> None:
    """Pending trades should be optional."""
    sections = extract_sections(
        StatementText(
            pages=(
                StatementPage(
                    number=1,
                    text="Portfolio Summary",
                ),
                StatementPage(
                    number=2,
                    text="Account Positions",
                ),
                StatementPage(
                    number=3,
                    text="Account Activity",
                ),
            ),
        )
    )

    assert sections.pending == ()


@pytest.mark.parametrize(
    ("missing", "match"),
    [
        (
            "Portfolio Summary",
            "Portfolio Summary section not found",
        ),
        (
            "Account Positions",
            "Account Positions section not found",
        ),
        (
            "Account Activity",
            "Account Activity section not found",
        ),
    ],
)
def test_extract_sections_rejects_missing_required_section(
    missing: str,
    match: str,
) -> None:
    """Required TD Ameritrade sections should fail explicitly."""
    markers = (
        "Portfolio Summary",
        "Account Positions",
        "Account Activity",
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
            StatementText(pages=pages),
        )


def test_extract_sections_allows_missing_positions_when_optional() -> None:
    """Transition statements may intentionally omit account positions."""
    text = StatementText(
        pages=(
            StatementPage(
                number=1,
                text="Portfolio Summary",
            ),
            StatementPage(
                number=2,
                text="Account Activity",
            ),
        ),
    )

    sections = extract_sections(
        text,
        require_positions=False,
    )

    assert sections.summary == (
        StatementPage(
            number=1,
            text="Portfolio Summary",
        ),
    )
    assert sections.positions == ()
    assert sections.activity == (
        StatementPage(
            number=2,
            text="Account Activity",
        ),
    )
    assert sections.pending == ()
