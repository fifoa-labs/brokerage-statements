"""
src/brokerage_statements/domain/amounts.py

Exact decimal conversion helpers for financial values and quantities.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from brokerage_statements.exceptions import InvalidDecimalError


def to_decimal(value: object) -> Decimal:
    """Return an exact finite Decimal from a supported input value."""
    if isinstance(value, bool):
        raise InvalidDecimalError(_invalid_decimal_message(value))

    if isinstance(value, Decimal):
        result = value
    elif isinstance(value, int):
        result = Decimal(value)
    elif isinstance(value, str):
        result = _decimal_from_string(value)
    else:
        raise InvalidDecimalError(_invalid_decimal_message(value))

    if not result.is_finite():
        raise InvalidDecimalError(_invalid_decimal_message(value))

    return result


def _decimal_from_string(value: str) -> Decimal:
    """Return a Decimal parsed from a non-empty string."""
    normalized = value.strip()

    if not normalized:
        raise InvalidDecimalError(_invalid_decimal_message(value))

    try:
        return Decimal(normalized)
    except InvalidOperation as exc:
        raise InvalidDecimalError(
            _invalid_decimal_message(value),
        ) from exc


def _invalid_decimal_message(value: object) -> str:
    """Return the standard invalid-decimal error message."""
    return (
        "Expected a finite Decimal, int, or decimal string; "
        f"received {value!r}."
    )
