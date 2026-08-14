"""
src/brokerage_statements/processors/charlesschwab/__init__.py

Charles Schwab statement processors and detection signatures.
"""

from __future__ import annotations

from brokerage_statements.domain import Broker
from brokerage_statements.processors.detection import BrokerSignature

from .monthly_2023 import Monthly2023Processor

BROKER_SIGNATURES = (
    BrokerSignature(
        name="charlesschwab.one",
        broker=Broker.CHARLES_SCHWAB,
        markers=(
            "Schwab One® Account of",
            "CharlesSchwab&Co.,Inc.MemberSIPC.",
        ),
    ),
)

__all__ = [
    "BROKER_SIGNATURES",
    "Monthly2023Processor",
]
