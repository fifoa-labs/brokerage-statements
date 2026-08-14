"""
tests/processors/charlesschwab/activity/test_rows.py

Tests for logical Charles Schwab transaction-row extraction.
"""

from __future__ import annotations

import pytest

from brokerage_statements.processors.charlesschwab.activity import rows
from brokerage_statements.processors.charlesschwab.activity.rows import (
    extract_activity_rows,
)
from brokerage_statements.processors.charlesschwab.sections import (
    StatementSections,
)
from brokerage_statements.text import StatementPage


def make_sections(
    *pages: StatementPage,
) -> StatementSections:
    """Return sections containing supplied transaction-detail pages."""
    summary = StatementPage(
        number=1,
        text="Account Summary",
    )
    positions = StatementPage(
        number=2,
        text="Positions - Summary",
    )
    transaction_summary = StatementPage(
        number=3,
        text="Transactions - Summary",
    )

    return StatementSections(
        summary=(summary,),
        positions=(positions,),
        transaction_summary=(transaction_summary,),
        transaction_details=pages,
    )


def test_extract_activity_rows_reconstructs_2023_transfer_rows() -> None:
    """Grouped Schwab transfer rows should inherit date and category."""
    page = StatementPage(
        number=4,
        text=(
            "Transaction Details\n"
            "Symbol/ Price/Rate Charges/ Realized\n"
            "Date Category Action CUSIP Description Quantity "
            "perShare($) Interest($) Amount($) Gain/(Loss)($)\n"
            "11/06 Deposit AccountTransfer "
            "TDA TO CS&CO TRANSFER 414.71\n"
            "Other AccountTransfer UAVS "
            "AGEAGLEAERIALSYSTEMSI 100.0000 0.1278 12.78\n"
            "Activity\n"
            "Other AccountTransfer DWACW "
            "DIGITALWORLDACQ28\n"
            "Activity WTFWARRANTSEXP 06/30/28\n"
            "110.0000 4.7600 523.60\n"
            "Other AccountTransfer PHMB "
            "PHARMACOMBIOVETINC 2,000,000.000\n"
            "Activity 0\n"
            "0.00\n"
            "11/29 Interest CreditInterest "
            "SCHWAB1INT10/30-11/28 0.23\n"
            "TotalTransactions $951.32 $0.00"
        ),
    )

    rows = extract_activity_rows(
        make_sections(page),
    )

    assert len(rows) == 5

    assert rows[0].date == "11/06"
    assert rows[0].category == "Deposit"
    assert rows[0].text == (
        "11/06 Deposit AccountTransfer TDA TO CS&CO TRANSFER 414.71"
    )

    assert rows[1].date == "11/06"
    assert rows[1].category == "Other Activity"
    assert rows[1].text == (
        "11/06 Other Activity AccountTransfer UAVS "
        "AGEAGLEAERIALSYSTEMSI 100.0000 0.1278 12.78"
    )

    assert rows[2].date == "11/06"
    assert rows[2].category == "Other Activity"
    assert rows[2].text == (
        "11/06 Other Activity AccountTransfer DWACW "
        "DIGITALWORLDACQ28 WTFWARRANTSEXP 06/30/28 "
        "110.0000 4.7600 523.60"
    )

    assert rows[3].date == "11/06"
    assert rows[3].category == "Other Activity"
    assert rows[3].text == (
        "11/06 Other Activity AccountTransfer PHMB "
        "PHARMACOMBIOVETINC 2,000,000.000 0 0.00"
    )

    assert rows[4].date == "11/29"
    assert rows[4].category == "Interest"
    assert rows[4].text == (
        "11/29 Interest CreditInterest SCHWAB1INT10/30-11/28 0.23"
    )


def test_extract_activity_rows_preserves_sequence() -> None:
    """Logical rows should receive deterministic source sequence."""
    page = StatementPage(
        number=4,
        text=(
            "Transaction Details\n"
            "11/06 Deposit AccountTransfer TRANSFER 10.00\n"
            "11/29 Interest CreditInterest INTEREST 0.23\n"
            "TotalTransactions $10.23"
        ),
    )

    rows = extract_activity_rows(
        make_sections(page),
    )

    assert [row.sequence for row in rows] == [
        1,
        2,
    ]


def test_extract_activity_rows_preserves_source_page() -> None:
    """Logical rows should span pages and retain their source page."""
    first = StatementPage(
        number=4,
        text=(
            "Transaction Details\n11/06 Deposit AccountTransfer TRANSFER 10.00"
        ),
    )
    second = StatementPage(
        number=5,
        text=(
            "11/29 Interest CreditInterest INTEREST 0.23\n"
            "TotalTransactions $10.23"
        ),
    )

    rows = extract_activity_rows(
        make_sections(
            first,
            second,
        )
    )

    assert [row.page_number for row in rows] == [
        4,
        5,
    ]


def test_extract_activity_rows_allows_no_transaction_details() -> None:
    """Statements without transaction details should yield no rows."""
    rows = extract_activity_rows(
        make_sections(),
    )

    assert rows == ()


def test_extract_activity_rows_stops_at_total_transactions() -> None:
    """Transaction totals and legal text must not enter activity rows."""
    page = StatementPage(
        number=4,
        text=(
            "Transaction Details\n"
            "11/29 Interest CreditInterest INTEREST 0.23\n"
            "TotalTransactions $0.23 $0.00\n"
            "DatecolumnrepresentstheSettlement/Processdate\n"
            "Terms and Conditions"
        ),
    )

    rows = extract_activity_rows(
        make_sections(page),
    )

    assert len(rows) == 1
    assert rows[0].text == ("11/29 Interest CreditInterest INTEREST 0.23")


def test_extract_activity_rows_rejects_unknown_dated_category() -> None:
    """Unknown dated transaction categories should fail explicitly."""
    page = StatementPage(
        number=4,
        text=(
            "Transaction Details\n"
            "11/29 Mystery UnsupportedActivity 10.00\n"
            "TotalTransactions $10.00"
        ),
    )

    with pytest.raises(
        ValueError,
        match="Unrecognized Charles Schwab transaction category",
    ):
        extract_activity_rows(
            make_sections(page),
        )


def test_extract_activity_rows_rejects_inherited_row_without_date() -> None:
    """Inherited Schwab rows require a preceding transaction date."""
    page = StatementPage(
        number=4,
        text=(
            "Transaction Details\n"
            "Other AccountTransfer TEST SECURITY 1.0000 1.00\n"
            "Activity\n"
            "TotalTransactions $1.00"
        ),
    )

    with pytest.raises(
        ValueError,
        match="transaction row has no inherited date",
    ):
        extract_activity_rows(
            make_sections(page),
        )


def test_extract_activity_rows_ignores_content_before_details() -> None:
    """Physical content before Transaction Details should be ignored."""
    page = StatementPage(
        number=4,
        text=(
            "Schwab One® Account of\n"
            "Statement Period\n"
            "Some unrelated content\n"
            "Transaction Details\n"
            "11/29 Interest CreditInterest INTEREST 0.23\n"
            "TotalTransactions $0.23"
        ),
    )

    result = extract_activity_rows(
        make_sections(page),
    )

    assert len(result) == 1
    assert result[0].text == ("11/29 Interest CreditInterest INTEREST 0.23")


def test_extract_activity_rows_ignores_noise_before_first_row() -> None:
    """Unknown non-row text before activity should not create a row."""
    page = StatementPage(
        number=4,
        text=(
            "Transaction Details\n"
            "Date Category Action Description\n"
            "11/29 Interest CreditInterest INTEREST 0.23\n"
            "TotalTransactions $0.23"
        ),
    )

    result = extract_activity_rows(
        make_sections(page),
    )

    assert len(result) == 1
    assert result[0].category == "Interest"


def test_extract_activity_rows_appends_normal_continuation() -> None:
    """Non-Other transaction continuation text should be preserved."""
    page = StatementPage(
        number=4,
        text=(
            "Transaction Details\n"
            "11/29 Interest CreditInterest\n"
            "SCHWAB1 INT 10/30-11/28\n"
            "0.23\n"
            "TotalTransactions $0.23"
        ),
    )

    result = extract_activity_rows(
        make_sections(page),
    )

    assert len(result) == 1
    assert result[0].text == (
        "11/29 Interest CreditInterest SCHWAB1 INT 10/30-11/28 0.23"
    )


def test_extract_activity_rows_supports_dated_category_only() -> None:
    """A dated physical row may contain only its category initially."""
    page = StatementPage(
        number=4,
        text=(
            "Transaction Details\n"
            "11/29 Interest\n"
            "CreditInterest INTEREST 0.23\n"
            "TotalTransactions $0.23"
        ),
    )

    result = extract_activity_rows(
        make_sections(page),
    )

    assert len(result) == 1
    assert result[0].text == ("11/29 Interest CreditInterest INTEREST 0.23")


def test_extract_activity_rows_supports_inherited_category_only() -> None:
    """An inherited category may receive its content afterward."""
    page = StatementPage(
        number=4,
        text=(
            "Transaction Details\n"
            "11/06 Deposit AccountTransfer TRANSFER 10.00\n"
            "Interest\n"
            "CreditInterest INTEREST 0.23\n"
            "TotalTransactions $10.23"
        ),
    )

    result = extract_activity_rows(
        make_sections(page),
    )

    assert len(result) == 2
    assert result[1].date == "11/06"
    assert result[1].category == "Interest"
    assert result[1].text == ("11/06 Interest CreditInterest INTEREST 0.23")


@pytest.mark.parametrize(
    ("category", "remainder", "expected"),
    [
        (
            "Interest",
            "CreditInterest 0.23",
            ("Interest", "CreditInterest 0.23"),
        ),
        (
            "Other",
            "Activity",
            ("Other Activity", ""),
        ),
        (
            "Other",
            "Activity WARRANTS EXP 06/30/28",
            (
                "Other Activity",
                "WARRANTS EXP 06/30/28",
            ),
        ),
        (
            "Other",
            "AccountTransfer TEST",
            (
                "Other",
                "AccountTransfer TEST",
            ),
        ),
    ],
)
def test_normalize_other_activity(
    category: str,
    remainder: str,
    expected: tuple[str, str],
) -> None:
    """Other Activity normalization should preserve supported forms."""
    assert (
        rows._normalize_other_activity(  # noqa: SLF001
            category,
            remainder,
        )
        == expected
    )


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (
            "Interest",
            ("Interest", ""),
        ),
        (
            "Interest CreditInterest 0.23",
            (
                "Interest",
                "CreditInterest 0.23",
            ),
        ),
        (
            "Completely Unknown",
            (
                None,
                "Completely Unknown",
            ),
        ),
    ],
)
def test_split_category(
    value: str,
    expected: tuple[str | None, str],
) -> None:
    """Physical category splitting should preserve all input forms."""
    assert rows._split_category(value) == expected  # noqa: SLF001


def test_append_current_rejects_incomplete_metadata() -> None:
    """Completed rows should require page and date metadata."""
    extracted: list[tuple[int, str, str, str]] = []

    with pytest.raises(
        ValueError,
        match="Incomplete Charles Schwab transaction row metadata",
    ):
        rows._append_current(  # noqa: SLF001
            extracted,
            page_number=None,
            date="11/06",
            category="Deposit",
            parts=["AccountTransfer TRANSFER 10.00"],
        )


def test_append_current_rejects_empty_activity_text() -> None:
    """Completed rows should require substantive activity text."""
    extracted: list[tuple[int, str, str, str]] = []

    with pytest.raises(
        ValueError,
        match="transaction row contains no activity text",
    ):
        rows._append_current(  # noqa: SLF001
            extracted,
            page_number=4,
            date="11/06",
            category="Deposit",
            parts=[],
        )


def test_extract_activity_rows_skips_known_header_lines() -> None:
    """Known Schwab table-header lines should be ignored."""
    page = StatementPage(
        number=4,
        text=(
            "Transaction Details\n"
            "Symbol/\n"
            "CUSIP Description Quantity\n"
            "Price/Rate\n"
            "perShare($)\n"
            "per Share($)\n"
            "Charges/\n"
            "Interest($) Amount($)\n"
            "Realized\n"
            "Gain/(Loss)($)\n"
            "11/29 Interest CreditInterest INTEREST 0.23\n"
            "TotalTransactions $0.23"
        ),
    )

    result = extract_activity_rows(
        make_sections(page),
    )

    assert len(result) == 1
    assert result[0].text == ("11/29 Interest CreditInterest INTEREST 0.23")


def test_extract_activity_rows_preserves_other_description_before_activity() -> (  # noqa: E501
    None
):
    """Other rows may contain description lines before Activity."""
    page = StatementPage(
        number=4,
        text=(
            "Transaction Details\n"
            "11/06 Other AccountTransfer TEST\n"
            "LONG SECURITY DESCRIPTION\n"
            "Activity WARRANTS EXP 06/30/28\n"
            "110.0000 4.7600 523.60\n"
            "TotalTransactions $523.60"
        ),
    )

    result = extract_activity_rows(
        make_sections(page),
    )

    assert len(result) == 1
    assert result[0].category == "Other Activity"
    assert result[0].text == (
        "11/06 Other Activity AccountTransfer TEST "
        "LONG SECURITY DESCRIPTION "
        "WARRANTS EXP 06/30/28 "
        "110.0000 4.7600 523.60"
    )
