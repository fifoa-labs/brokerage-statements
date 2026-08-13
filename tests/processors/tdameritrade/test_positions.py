"""
tests/processors/tdameritrade/test_positions.py

Tests for TD Ameritrade closing-position parsing.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from brokerage_statements.domain import (
    Security,
    StatementSource,
    SymbolSecurity,
)
from brokerage_statements.processors.tdameritrade.positions import (
    parse_positions,
)
from brokerage_statements.processors.tdameritrade.sections import (
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
        text="Portfolio Summary",
    )
    activity = StatementPage(
        number=3,
        text="Account Activity",
    )

    return StatementSections(
        summary=(summary,),
        positions=pages,
        activity=(activity,),
        pending=(),
    )


def test_parse_positions_preserves_real_td_row_shape() -> None:
    """Real TD rows should preserve symbol and quantity."""
    page = StatementPage(
        number=4,
        text="\n".join(  # noqa: FLY002
            (
                "Account Positions",
                (
                    "ASTROTECH ASTC 1,000 $ 2.60 $2,600.00 "
                    "03/27/20 $ 3,780.00 $ 3.78 "
                    "$ (1,180.00) $ - -"
                ),
                "CORPORATION",
                "COM",
            )
        ),
    )

    positions = parse_positions(
        make_source(),
        make_sections(page),
        processor_name="tdameritrade.monthly_2020",
    )

    assert len(positions) == 1

    position = positions[0]

    assert symbol_of(position.security) == "ASTC"
    assert position.quantity == Decimal("1000")
    assert position.evidence.source == make_source()
    assert position.evidence.page == 4
    assert position.evidence.section == "Account Positions"
    assert position.evidence.processor == "tdameritrade.monthly_2020"
    assert position.evidence.sequence == 1
    assert position.evidence.raw_text == (
        "ASTROTECH ASTC 1,000 $ 2.60 $2,600.00 "
        "03/27/20 $ 3,780.00 $ 3.78 "
        "$ (1,180.00) $ - -"
    )


def test_parse_positions_preserves_real_march_2020_positions() -> None:
    """March 2020 closing positions should retain statement order."""
    page = StatementPage(
        number=4,
        text="\n".join(  # noqa: FLY002
            (
                "Account Positions",
                (
                    "ASTROTECH ASTC 1,000 $ 2.60 $2,600.00 "
                    "03/27/20 $ 3,780.00 $ 3.78 "
                    "$ (1,180.00) $ - -"
                ),
                "CORPORATION",
                "COM",
                (
                    "DIREXION SHARES ETF JNUG 1,000 3.97 "
                    "3,970.00 03/27/20 4,670.00 4.67 "
                    "(700.00) 175.00 4.4%"
                ),
                "TRUST",
                "DAILY JR GLD MIN ETF",
                (
                    "HERTZ GLOBAL HTZ 400 6.18 2,472.00 "
                    "03/25/20 3,142.00 7.86 "
                    "(670.00) - -"
                ),
                "HOLDINGS INC",
                "COM",
                (
                    "NOVABAY NBY 700 0.5997 419.79 "
                    "03/26/20 539.00 0.77 "
                    "(119.21) - -"
                ),
                "PHARMACEUTICALS INC",
                "COM",
                (
                    "UNITED STATES OIL USO 1,000 4.21 "
                    "4,210.00 03/26/20 4,830.00 4.83 "
                    "(620.00) - -"
                ),
                "FUND LP",
                "UNITS ETF",
            )
        ),
    )

    positions = parse_positions(
        make_source(),
        make_sections(page),
        processor_name="tdameritrade.monthly_2020",
    )

    assert [symbol_of(position.security) for position in positions] == [
        "ASTC",
        "JNUG",
        "HTZ",
        "NBY",
        "USO",
    ]
    assert [position.quantity for position in positions] == [
        Decimal("1000"),
        Decimal("1000"),
        Decimal("400"),
        Decimal("700"),
        Decimal("1000"),
    ]
    assert [position.evidence.sequence for position in positions] == [
        1,
        2,
        3,
        4,
        5,
    ]


def test_parse_positions_supports_na_price_and_market_value() -> None:
    """Positions remain valid when TD reports unavailable pricing."""
    page = StatementPage(
        number=4,
        text="\n".join(  # noqa: FLY002
            (
                "Account Positions",
                (
                    "PHARMACOM BIOVET INC PHMB "
                    "2,000,000 NA NA 02/08/21 "
                    "2,430.95 - (2,430.95) - -"
                ),
                "COM",
            )
        ),
    )

    positions = parse_positions(
        make_source(),
        make_sections(page),
        processor_name="tdameritrade.monthly_2020",
    )

    assert len(positions) == 1
    assert symbol_of(positions[0].security) == "PHMB"
    assert positions[0].quantity == Decimal("2000000")


def test_parse_positions_supports_decimal_quantity() -> None:
    """Position quantities may contain decimal precision."""
    page = StatementPage(
        number=4,
        text=(
            "TEST SECURITY TEST 12.5000 10.00 125.00 "
            "03/27/20 100.00 8.00 25.00 - -"
        ),
    )

    positions = parse_positions(
        make_source(),
        make_sections(page),
        processor_name="tdameritrade.monthly_2020",
    )

    assert len(positions) == 1
    assert symbol_of(positions[0].security) == "TEST"
    assert positions[0].quantity == Decimal("12.5000")


def test_parse_positions_supports_multiple_pages() -> None:
    """Positions spanning several pages should remain ordered."""
    first = StatementPage(
        number=4,
        text=(
            "ASTROTECH ASTC 1,000 2.60 2,600.00 "
            "03/27/20 3,780.00 3.78 "
            "(1,180.00) - -"
        ),
    )
    second = StatementPage(
        number=5,
        text=(
            "UNITED STATES OIL USO 1,000 4.21 "
            "4,210.00 03/26/20 4,830.00 4.83 "
            "(620.00) - -"
        ),
    )

    positions = parse_positions(
        make_source(),
        make_sections(first, second),
        processor_name="tdameritrade.monthly_2020",
    )

    assert [symbol_of(position.security) for position in positions] == [
        "ASTC",
        "USO",
    ]
    assert [position.evidence.page for position in positions] == [
        4,
        5,
    ]
    assert [position.evidence.sequence for position in positions] == [
        1,
        2,
    ]


def test_parse_positions_ignores_headers_descriptions_and_totals() -> None:
    """Non-position rows should not become reported positions."""
    page = StatementPage(
        number=4,
        text="\n".join(  # noqa: FLY002
            (
                "Account Positions",
                "Symbol/ Current Market Purchase Cost Average",
                (
                    "Investment Description CUSIP Quantity "
                    "Price Value Date Basis Cost"
                ),
                "Stocks - Cash",
                "ASTROTECH CORPORATION",
                "COM",
                "Total Stocks $13,671.79 $16,961.00 $(3,289.21)",
                "Total Cash Account $13,671.79 $16,961.00",
            )
        ),
    )

    positions = parse_positions(
        make_source(),
        make_sections(page),
        processor_name="tdameritrade.monthly_2020",
    )

    assert positions == ()


def test_parse_positions_allows_no_reported_positions() -> None:
    """A valid positions section may contain no securities."""
    page = StatementPage(
        number=4,
        text="\n".join(  # noqa: FLY002
            (
                "Account Positions",
                "Symbol/ Current Market Purchase Cost Average",
                "Total Cash Account $0.00",
            )
        ),
    )

    positions = parse_positions(
        make_source(),
        make_sections(page),
        processor_name="tdameritrade.monthly_2020",
    )

    assert positions == ()
