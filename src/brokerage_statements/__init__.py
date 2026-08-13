"""
src/brokerage_statements/__init__.py

Public package interface for brokerage-statements.
"""

from __future__ import annotations

from .api import parse_statement

__all__ = [
    "parse_statement",
]
