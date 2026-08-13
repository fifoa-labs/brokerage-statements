"""
src/brokerage_statements/reference/__init__.py

Reference data and security identifier resolution.
"""

from __future__ import annotations

from .identifiers import resolve_symbol

__all__ = [
    "resolve_symbol",
]
