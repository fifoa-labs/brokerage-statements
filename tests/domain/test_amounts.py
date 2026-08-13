"""
tests/domain/test_amounts.py

Tests for exact brokerage decimal conversion.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest

from brokerage_statements.domain import to_decimal
from brokerage_statements.exceptions import InvalidDecimalError


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (Decimal("12.34"), Decimal("12.34")),
        (Decimal("-12.34"), Decimal("-12.34")),
        (Decimal("0"), Decimal("0")),
        (12, Decimal("12")),
        (-12, Decimal("-12")),
        (0, Decimal("0")),
        ("12.34", Decimal("12.34")),
        ("-12.34", Decimal("-12.34")),
        ("0", Decimal("0")),
        ("  12.34  ", Decimal("12.34")),
        ("0.00000001", Decimal("0.00000001")),
        ("166.666666666666666666", Decimal("166.666666666666666666")),
    ],
)
def test_to_decimal_accepts_exact_values(
    value: Decimal | int | str,
    expected: Decimal,
) -> None:
    """Supported values should convert without losing precision."""
    assert to_decimal(value) == expected


@pytest.mark.parametrize(
    "value",
    [
        Decimal("NaN"),
        Decimal("Infinity"),
        Decimal("-Infinity"),
        "NaN",
        "Infinity",
        "-Infinity",
        "",
        "   ",
        "not-a-number",
    ],
)
def test_to_decimal_rejects_invalid_decimal_values(
    value: Decimal | str,
) -> None:
    """Invalid and non-finite decimal values should be rejected."""
    with pytest.raises(
        InvalidDecimalError,
        match="Expected a finite Decimal",
    ):
        to_decimal(value)


@pytest.mark.parametrize(
    "value",
    [
        1.25,
        -0.0,
        True,
        False,
        None,
        object(),
    ],
)
def test_to_decimal_rejects_unsupported_runtime_types(
    value: Any,
) -> None:
    """Unsupported runtime values should fail explicitly."""
    with pytest.raises(
        InvalidDecimalError,
        match="Expected a finite Decimal",
    ):
        to_decimal(value)
