"""
tests/test_init.py

Tests for the brokerage-statements package interface.
"""

from __future__ import annotations

import brokerage_statements


def test_package_imports() -> None:
    """The public package should import successfully."""
    assert brokerage_statements.__name__ == "brokerage_statements"
