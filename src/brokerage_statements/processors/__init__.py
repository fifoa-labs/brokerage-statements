"""
src/brokerage_statements/processors/__init__.py

Statement processor contracts and deterministic registry selection.
"""

from __future__ import annotations

from .base import ProcessorMatch, StatementProcessor
from .registry import ProcessorRegistry

__all__ = [
    "ProcessorMatch",
    "ProcessorRegistry",
    "StatementProcessor",
]
