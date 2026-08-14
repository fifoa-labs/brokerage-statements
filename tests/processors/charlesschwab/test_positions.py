"""
tests/processors/charlesschwab/test_positions.py

Tests for Charles Schwab closing-position parsing.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from brokerage_statements.domain import (
    Security,
    StatementSource,
    SymbolSecurity,
)
from brokerage_statements.processors.charlesschwab.positions import (
    parse_positions,
)
from brokerage_statements.processors.charlesschwab.sections import (
    StatementSections,
)
from brokerage_statements.text import StatementPage


def symbol_of(security: Security) -> str:
    """Return the symbol for a symbol-backed security."""
    assert isinstance(security, SymbolSecurity)
    return security.symbol


def make_source() -> StatementSource:
    """Return reusable statement source identity."""
    return StatementSource(
        path=Path("statement.pdf"),
        sha256="abc123",
    )


def make_sections(
    *pages: StatementPage,
) -> StatementSections:
    """Return statement sections containing position pages."""
    summary = StatementPage(
        number=1,
        text="Account Summary",
    )
    transactions = StatementPage(
        number=4,
        text="Transactions - Summary",
    )

    return StatementSections(
        summary=(summary,),
        positions=pages,
        transaction_summary=(transactions,),
        transaction_details=(),
    )


def test_parse_positions_preserves_2023_row_shapes() -> None:
    """Observed 2023 position grammars should retain quantities."""
    page = StatementPage(
        number=3,
        text="\n".join(  # noqa: FLY002
            (
                "Positions - Equities",
                (
                    "TEST SAMPLESECURITYI "
                    "100.0000 0.12260 12.26 "
                    "1,510.77 (1,498.51) N/A 0.00 1%"
                ),
                (
                    "ZERO ZEROVALUESECURITY "
                    "2,000,000.0000 0.00000 0.00 "
                    "2,430.95 (2,430.95) N/A 0.00"
                ),
                ("TotalEquities $12.26 $3,941.72 ($3,929.46) $0.00 1%"),
                "Positions - Other Assets",
                (
                    "WRTS SAMPLEACQ28WTF, "
                    "110.0000 5.98000 657.80 "
                    "5,920.84 (5,263.04) N/A N/A 61%"
                ),
                "WARRANTSEXP 06/30/28",
                ("TotalOtherAssets $657.80 $5,920.84 ($5,263.04) $0.00 61%"),
                "Transactions - Summary",
            )
        ),
    )

    positions = parse_positions(
        make_source(),
        make_sections(page),
        processor_name="charlesschwab.monthly_2023",
    )

    assert [symbol_of(position.security) for position in positions] == [
        "TEST",
        "ZERO",
        "WRTS",
    ]
    assert [position.quantity for position in positions] == [
        Decimal("100.0000"),
        Decimal("2000000.0000"),
        Decimal("110.0000"),
    ]


def test_parse_positions_preserves_evidence() -> None:
    """Normalized positions should retain exact source evidence."""
    row = (
        "TEST SAMPLESECURITYI "
        "100.0000 0.12260 12.26 "
        "1,510.77 (1,498.51) N/A 0.00 1%"
    )
    page = StatementPage(
        number=3,
        text="\n".join(  # noqa: FLY002
            (
                "Positions - Equities",
                row,
                "TotalEquities $12.26",
            )
        ),
    )

    positions = parse_positions(
        make_source(),
        make_sections(page),
        processor_name="charlesschwab.monthly_2023",
    )

    assert len(positions) == 1

    evidence = positions[0].evidence

    assert evidence.source == make_source()
    assert evidence.page == 3
    assert evidence.section == "Positions - Equities"
    assert evidence.raw_text == row
    assert evidence.processor == "charlesschwab.monthly_2023"
    assert evidence.sequence == 1


def test_parse_positions_allows_only_other_assets() -> None:
    """A Schwab statement need not contain an equities section."""
    page = StatementPage(
        number=3,
        text="\n".join(  # noqa: FLY002
            (
                "Positions - Other Assets",
                (
                    "WRTS SAMPLEMEDIA&TEC29WTS, "
                    "110.0000 4.44000 488.40 "
                    "5,920.84 (5,432.44) N/A N/A 54%"
                ),
                "WARRANTSEXERCISE",
                "EXP:03/23/29",
                "TotalOtherAssets $488.40 $5,920.84",
                "Transactions - Summary",
            )
        ),
    )

    positions = parse_positions(
        make_source(),
        make_sections(page),
        processor_name="charlesschwab.monthly_2023",
    )

    assert len(positions) == 1
    assert symbol_of(positions[0].security) == "WRTS"
    assert positions[0].quantity == Decimal("110.0000")


def test_parse_positions_preserves_order_across_asset_sections() -> None:
    """Different Schwab asset sections should retain statement order."""
    page = StatementPage(
        number=3,
        text="\n".join(  # noqa: FLY002
            (
                "Positions - Equities",
                (
                    "FIRST FIRSTSECURITY "
                    "25.0000 1.00000 25.00 "
                    "20.00 5.00 N/A 0.00 5%"
                ),
                "TotalEquities $25.00",
                "Positions - Other Assets",
                (
                    "SECOND SECONDSECURITY "
                    "10.0000 2.00000 20.00 "
                    "15.00 5.00 N/A N/A 4%"
                ),
                "TotalOtherAssets $20.00",
            )
        ),
    )

    positions = parse_positions(
        make_source(),
        make_sections(page),
        processor_name="charlesschwab.monthly_2023",
    )

    assert [symbol_of(position.security) for position in positions] == [
        "FIRST",
        "SECOND",
    ]
    assert [position.evidence.sequence for position in positions] == [
        1,
        2,
    ]


def test_parse_positions_supports_section_continuation_page() -> None:
    """A position table may continue onto a later statement page."""
    first = StatementPage(
        number=3,
        text="\n".join(  # noqa: FLY002
            (
                "Positions - Equities",
                (
                    "FIRST FIRSTSECURITY "
                    "25.0000 1.00000 25.00 "
                    "20.00 5.00 N/A 0.00 5%"
                ),
            )
        ),
    )
    second = StatementPage(
        number=4,
        text="\n".join(  # noqa: FLY002
            (
                (
                    "SECOND SECONDSECURITY "
                    "10.0000 2.00000 20.00 "
                    "15.00 5.00 N/A 0.00 4%"
                ),
                "TotalEquities $45.00",
            )
        ),
    )

    positions = parse_positions(
        make_source(),
        make_sections(
            first,
            second,
        ),
        processor_name="charlesschwab.monthly_2023",
    )

    assert [symbol_of(position.security) for position in positions] == [
        "FIRST",
        "SECOND",
    ]
    assert [position.evidence.page for position in positions] == [
        3,
        4,
    ]


def test_parse_positions_ignores_non_position_content() -> None:
    """Cash, headers, totals, and descriptions are not positions."""
    page = StatementPage(
        number=3,
        text="\n".join(  # noqa: FLY002
            (
                "Positions - Summary",
                "Cash and Cash Investments",
                ("Cash 418.15 418.15 0.00 0.00 46%"),
                "Positions - Other Assets",
                (
                    "Symbol Description Quantity Price($) "
                    "Market Value($) CostBasis($)"
                ),
                (
                    "WRTS SAMPLEACQ28WTF, "
                    "110.0000 4.44000 488.40 "
                    "5,920.84 (5,432.44) N/A N/A 54%"
                ),
                "WARRANTSEXERCISE",
                "EXP:03/23/29",
                "TotalOtherAssets $488.40 $5,920.84",
                "Transactions - Summary",
            )
        ),
    )

    positions = parse_positions(
        make_source(),
        make_sections(page),
        processor_name="charlesschwab.monthly_2023",
    )

    assert len(positions) == 1
    assert symbol_of(positions[0].security) == "WRTS"


def test_parse_positions_rejects_missing_security_section() -> None:
    """Missing security tables must not imply zero positions."""
    page = StatementPage(
        number=3,
        text="\n".join(  # noqa: FLY002
            (
                "Positions - Summary",
                "Cash and Cash Investments",
                "Transactions - Summary",
            )
        ),
    )

    with pytest.raises(
        ValueError,
        match="Charles Schwab security position section not found",
    ):
        parse_positions(
            make_source(),
            make_sections(page),
            processor_name="charlesschwab.monthly_2023",
        )


def test_parse_positions_rejects_empty_security_sections() -> None:
    """A discovered security table should yield reported positions."""
    page = StatementPage(
        number=3,
        text="\n".join(  # noqa: FLY002
            (
                "Positions - Other Assets",
                "Symbol Description Quantity Price($)",
                "TotalOtherAssets $0.00",
            )
        ),
    )

    with pytest.raises(
        ValueError,
        match=(
            "Charles Schwab security position sections "
            "contain no parsed positions"
        ),
    ):
        parse_positions(
            make_source(),
            make_sections(page),
            processor_name="charlesschwab.monthly_2023",
        )


def test_parse_positions_rejects_unrecognized_candidate_row() -> None:
    """Malformed numeric position rows should fail explicitly."""
    row = "TEST SAMPLESECURITY 100.0000 5.00000 500.00 400.00 UNKNOWN 100.00"
    page = StatementPage(
        number=3,
        text="\n".join(  # noqa: FLY002
            (
                "Positions - Equities",
                row,
                "TotalEquities $500.00",
            )
        ),
    )

    with pytest.raises(
        ValueError,
        match="Unrecognized Charles Schwab position row",
    ):
        parse_positions(
            make_source(),
            make_sections(page),
            processor_name="charlesschwab.monthly_2023",
        )
