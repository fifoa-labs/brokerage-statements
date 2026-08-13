"""
tests/processors/charlesschwab/test_init.py

Tests for Charles Schwab processor package exports and signatures.
"""

from __future__ import annotations

from brokerage_statements.domain import Broker
from brokerage_statements.processors.charlesschwab import BROKER_SIGNATURES
from brokerage_statements.text import StatementPage, StatementText


def test_broker_signature_matches_schwab_statement() -> None:
    """Schwab package signature should match observed statement text."""
    text = StatementText(
        pages=(
            StatementPage(
                number=1,
                text=(
                    "Schwab One® Account of\nCharlesSchwab&Co.,Inc.MemberSIPC."
                ),
            ),
        ),
    )

    signature = BROKER_SIGNATURES[0]

    assert signature.broker is Broker.CHARLES_SCHWAB
    assert signature.matches(text)
