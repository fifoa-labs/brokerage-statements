"""
src/brokerage_statements/processors/__init__.py

Statement processor contracts, detection, and deterministic selection.
"""

from __future__ import annotations

from .base import ProcessorMatch, StatementProcessor
from .detection import BrokerDetector, BrokerSignature
from .registry import ProcessorRegistry

__all__ = [
    "BrokerDetector",
    "BrokerSignature",
    "ProcessorMatch",
    "ProcessorRegistry",
    "StatementProcessor",
]
