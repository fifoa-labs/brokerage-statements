"""
tests/processors/tdameritrade/activity/test_rows.py

Tests for logical TD Ameritrade account-activity row extraction.
"""

from __future__ import annotations

from brokerage_statements.processors.tdameritrade.activity.rows import (
    extract_activity_rows,
)
from brokerage_statements.text import StatementPage

from ._helpers import make_sections


def test_extract_activity_rows_joins_wrapped_lines() -> None:
    """Wrapped source lines should form one logical activity row."""
    rows = extract_activity_rows(
        make_sections(
            StatementPage(
                number=5,
                text=(
                    "Account Activity\n"
                    "03/24/20 03/26/20 Cash Buy - Securities Purchased "
                    "BARCLAYS BANK PLC VXX 100 44.73 "
                    "(4,473.00) (4,019.36)\n"
                    "IPATH B SHRT TRM ETN"
                ),
            )
        )
    )

    assert len(rows) == 1

    row = rows[0]

    assert row.page_number == 5
    assert row.sequence == 1
    assert row.text == (
        "03/24/20 03/26/20 Cash Buy - Securities Purchased "
        "BARCLAYS BANK PLC VXX 100 44.73 "
        "(4,473.00) (4,019.36) "
        "IPATH B SHRT TRM ETN"
    )


def test_extract_activity_rows_preserves_sequence() -> None:
    """Logical rows should receive deterministic source sequence."""
    rows = extract_activity_rows(
        make_sections(
            StatementPage(
                number=5,
                text=(
                    "Account Activity\n"
                    "03/17/20 03/17/20 Cash Journal - Other "
                    "MOVE CASH BALANCE TO MARGIN "
                    "- - 0.00 (2,000.00) 0.00\n"
                    "03/19/20 03/20/20 Cash Buy - Securities Purchased "
                    "DIREXION SHARES ETF TRUST NUGT "
                    "200 5.52 (1,104.00) (104.00)"
                ),
            )
        )
    )

    assert len(rows) == 2
    assert rows[0].sequence == 1
    assert rows[1].sequence == 2


def test_extract_activity_rows_preserves_order_across_pages() -> None:
    """Logical rows should retain page and statement order."""
    rows = extract_activity_rows(
        make_sections(
            StatementPage(
                number=5,
                text=(
                    "Account Activity\n"
                    "03/19/20 03/20/20 Cash Buy - Securities Purchased "
                    "TEST SECURITY TEST 1 10.00 "
                    "(10.00) (10.00)"
                ),
            ),
            StatementPage(
                number=6,
                text=(
                    "Account Activity\n"
                    "03/20/20 03/23/20 Cash Sell - Securities Sold "
                    "TEST SECURITY TEST 1- 11.00 "
                    "11.00 1.00"
                ),
            ),
        )
    )

    assert len(rows) == 2
    assert rows[0].page_number == 5
    assert rows[0].sequence == 1
    assert rows[1].page_number == 6
    assert rows[1].sequence == 2


def test_extract_activity_rows_ignores_page_footer() -> None:
    """TD page footers should not contaminate logical rows."""
    rows = extract_activity_rows(
        make_sections(
            StatementPage(
                number=5,
                text=(
                    "Account Activity\n"
                    "03/19/20 03/20/20 Cash Buy - Securities Purchased "
                    "TEST SECURITY TEST 1 10.00 "
                    "(10.00) (10.00)\n"
                    "page 3 of 9"
                ),
            )
        )
    )

    assert len(rows) == 1
    assert "page 3 of 9" not in rows[0].text


def test_extract_activity_rows_stops_at_closing_balance() -> None:
    """Closing balance should terminate the active source row."""
    rows = extract_activity_rows(
        make_sections(
            StatementPage(
                number=5,
                text=(
                    "Account Activity\n"
                    "09/30/21 09/30/21 Cash Div/Int - Income "
                    "INTEREST CREDIT - - 0.00 0.02 2,887.83\n"
                    "Closing Balance $2,887.83\n"
                    "Unrelated text after activity"
                ),
            )
        )
    )

    assert len(rows) == 1
    assert "Closing Balance" not in rows[0].text
    assert "Unrelated text" not in rows[0].text


def test_extract_activity_rows_allows_no_rows() -> None:
    """An activity section without transactions should be empty."""
    rows = extract_activity_rows(
        make_sections(
            StatementPage(
                number=5,
                text=(
                    "Account Activity\n"
                    "Trade Date Settle Date\n"
                    "Closing Balance $0.00"
                ),
            )
        )
    )

    assert rows == ()
