"""
src/brokerage_statements/reference/identifiers.py

Reference resolution for brokerage security identifiers.
"""

from __future__ import annotations

import re

from brokerage_statements.exceptions import UnresolvedSecurityError

_CUSIP_PATTERN = re.compile(
    r"^[A-Z0-9]{9}$",
)

_SYMBOL_PATTERN = re.compile(
    r"^[A-Z][A-Z0-9.-]*$",
)

_CUSIP_TO_SYMBOL = {
    "25460E166": "JNUG",
    "25460G831": "JNUG",
    "91232N108": "USO",
    "91232N207": "USO",
    "98420U604": "XSPA",
    "98420U703": "XSPA",
    "Y73760301": "SHIP",
    "Y73760194": "SHIP",
    "74347Y839": "UVXY",
    "74347Y771": "UVXY",
}


def resolve_symbol(identifier: str) -> str:
    """Resolve a statement security identifier to a canonical symbol."""
    normalized = identifier.strip().upper()

    if not normalized:
        msg = "security identifier must not be empty."
        raise UnresolvedSecurityError(msg)

    known_symbol = _CUSIP_TO_SYMBOL.get(normalized)

    if known_symbol is not None:
        return known_symbol

    if _looks_like_cusip(normalized):
        msg = f"Unresolved security identifier: {normalized!r}."
        raise UnresolvedSecurityError(msg)

    if _SYMBOL_PATTERN.fullmatch(normalized) is None:
        msg = f"Invalid security identifier: {normalized!r}."
        raise UnresolvedSecurityError(msg)

    return normalized


def _looks_like_cusip(identifier: str) -> bool:
    """Return whether an identifier has CUSIP-like structure."""
    if _CUSIP_PATTERN.fullmatch(identifier) is None:
        return False

    return any(character.isdigit() for character in identifier)
