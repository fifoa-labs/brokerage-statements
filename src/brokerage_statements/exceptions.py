"""
src/brokerage_statements/exceptions.py

Package-specific exception hierarchy for brokerage statement processing.
"""

from __future__ import annotations


class BrokerageStatementsError(Exception):
    """Base exception for brokerage-statements."""
