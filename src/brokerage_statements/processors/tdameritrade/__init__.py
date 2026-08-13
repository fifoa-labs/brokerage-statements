"""
src/brokerage_statements/processors/tdameritrade/__init__.py

TD Ameritrade statement processors and detection signatures.
"""

from __future__ import annotations

from brokerage_statements.domain import Broker
from brokerage_statements.processors.detection import BrokerSignature

from .monthly_2020 import Monthly2020Processor
from .transition_2023 import Transition2023Processor

BROKER_SIGNATURES = (
    BrokerSignature(
        name="tdameritrade.monthly",
        broker=Broker.TD_AMERITRADE,
        markers=(
            "Statement for Account #",
            "TD AMERITRADE",
            "TD Ameritrade Clearing, Inc., Member SIPC",
        ),
    ),
)

__all__ = [
    "BROKER_SIGNATURES",
    "Monthly2020Processor",
    "Transition2023Processor",
]
