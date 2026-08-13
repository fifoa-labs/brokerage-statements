"""
tests/processors/test_detection.py

Tests for deterministic brokerage institution detection.
"""

from __future__ import annotations

import pytest

from brokerage_statements.domain import Broker
from brokerage_statements.exceptions import (
    AmbiguousBrokerError,
    UnsupportedBrokerError,
)
from brokerage_statements.processors import (
    BrokerDetector,
    BrokerSignature,
)
from brokerage_statements.text import (
    StatementPage,
    StatementText,
)


def make_text(value: str) -> StatementText:
    """Return one-page statement text."""
    return StatementText(
        pages=(
            StatementPage(
                number=1,
                text=value,
            ),
        ),
    )


def test_broker_signature_preserves_values() -> None:
    """Broker signatures should preserve normalized metadata."""
    signature = BrokerSignature(
        name="  td.primary  ",
        broker=Broker.TD_AMERITRADE,
        markers=(" TD Marker ", " Account Summary "),
    )

    assert signature.name == "td.primary"
    assert signature.broker is Broker.TD_AMERITRADE
    assert signature.markers == (
        "TD Marker",
        "Account Summary",
    )


def test_broker_signature_matches_all_markers() -> None:
    """A signature should require every configured marker."""
    signature = BrokerSignature(
        name="td.primary",
        broker=Broker.TD_AMERITRADE,
        markers=(
            "TD Marker",
            "Account Summary",
        ),
    )

    assert signature.matches(
        make_text("td marker\nACCOUNT SUMMARY"),
    )


def test_broker_signature_rejects_partial_match() -> None:
    """Missing signature markers should reject the source."""
    signature = BrokerSignature(
        name="td.primary",
        broker=Broker.TD_AMERITRADE,
        markers=(
            "TD Marker",
            "Account Summary",
        ),
    )

    assert not signature.matches(
        make_text("TD Marker"),
    )


def test_broker_signature_rejects_empty_name() -> None:
    """Broker signatures should require stable names."""
    with pytest.raises(
        ValueError,
        match="broker signature name must not be empty",
    ):
        BrokerSignature(
            name=" ",
            broker=Broker.TD_AMERITRADE,
            markers=("marker",),
        )


def test_broker_signature_rejects_empty_markers() -> None:
    """Broker signatures should require source markers."""
    with pytest.raises(
        ValueError,
        match="broker signature markers must not be empty",
    ):
        BrokerSignature(
            name="td.primary",
            broker=Broker.TD_AMERITRADE,
            markers=(),
        )


def test_broker_signature_rejects_blank_marker() -> None:
    """Broker signatures should reject blank markers."""
    with pytest.raises(
        ValueError,
        match="must not contain empty values",
    ):
        BrokerSignature(
            name="td.primary",
            broker=Broker.TD_AMERITRADE,
            markers=("marker", " "),
        )


def test_detector_preserves_signature_order() -> None:
    """Detector configuration should remain immutable and ordered."""
    first = BrokerSignature(
        name="td.primary",
        broker=Broker.TD_AMERITRADE,
        markers=("TD Marker",),
    )
    second = BrokerSignature(
        name="schwab.primary",
        broker=Broker.CHARLES_SCHWAB,
        markers=("Schwab Marker",),
    )

    detector = BrokerDetector([first, second])

    assert detector.signatures == (first, second)


def test_detector_detects_td_ameritrade() -> None:
    """TD-specific signatures should identify TD Ameritrade."""
    detector = BrokerDetector(
        [
            BrokerSignature(
                name="td.primary",
                broker=Broker.TD_AMERITRADE,
                markers=(
                    "TD Marker",
                    "TD Account Summary",
                ),
            ),
        ]
    )

    broker = detector.detect(
        make_text(
            "TD Marker\nTD Account Summary",
        )
    )

    assert broker is Broker.TD_AMERITRADE


def test_detector_detects_charles_schwab() -> None:
    """Schwab-specific signatures should identify Schwab."""
    detector = BrokerDetector(
        [
            BrokerSignature(
                name="schwab.primary",
                broker=Broker.CHARLES_SCHWAB,
                markers=(
                    "Schwab Marker",
                    "Schwab Account Summary",
                ),
            ),
        ]
    )

    broker = detector.detect(
        make_text(
            "Schwab Marker\nSchwab Account Summary",
        )
    )

    assert broker is Broker.CHARLES_SCHWAB


def test_detector_allows_multiple_signatures_for_same_broker() -> None:
    """Several matching revisions may still identify one broker."""
    detector = BrokerDetector(
        [
            BrokerSignature(
                name="td.old",
                broker=Broker.TD_AMERITRADE,
                markers=("TD Marker",),
            ),
            BrokerSignature(
                name="td.new",
                broker=Broker.TD_AMERITRADE,
                markers=("Account Summary",),
            ),
        ]
    )

    broker = detector.detect(
        make_text(
            "TD Marker\nAccount Summary",
        )
    )

    assert broker is Broker.TD_AMERITRADE


def test_detector_rejects_unknown_broker() -> None:
    """Unrecognized statements should fail explicitly."""
    detector = BrokerDetector(
        [
            BrokerSignature(
                name="td.primary",
                broker=Broker.TD_AMERITRADE,
                markers=("TD Marker",),
            ),
        ]
    )

    with pytest.raises(
        UnsupportedBrokerError,
        match="No supported broker signature matched",
    ):
        detector.detect(
            make_text("Unknown statement"),
        )


def test_detector_rejects_ambiguous_broker() -> None:
    """Statements matching several brokers should fail."""
    detector = BrokerDetector(
        [
            BrokerSignature(
                name="td.primary",
                broker=Broker.TD_AMERITRADE,
                markers=("TD Marker",),
            ),
            BrokerSignature(
                name="schwab.primary",
                broker=Broker.CHARLES_SCHWAB,
                markers=("Schwab Marker",),
            ),
        ]
    )

    with pytest.raises(
        AmbiguousBrokerError,
        match=(
            "Multiple broker signatures matched statement text: "
            "charlesschwab, tdameritrade"
        ),
    ):
        detector.detect(
            make_text(
                "TD Marker\nSchwab Marker",
            ),
        )


def test_detector_rejects_duplicate_signature_names() -> None:
    """Signature names should uniquely identify detection rules."""
    first = BrokerSignature(
        name="duplicate",
        broker=Broker.TD_AMERITRADE,
        markers=("TD Marker",),
    )
    second = BrokerSignature(
        name="duplicate",
        broker=Broker.CHARLES_SCHWAB,
        markers=("Schwab Marker",),
    )

    with pytest.raises(
        ValueError,
        match="Broker signature names must be unique",
    ):
        BrokerDetector([first, second])


def test_detection_is_independent_of_signature_order() -> None:
    """Detection outcome should not depend on registration order."""
    td = BrokerSignature(
        name="td.primary",
        broker=Broker.TD_AMERITRADE,
        markers=("TD Marker",),
    )
    unrelated = BrokerSignature(
        name="schwab.primary",
        broker=Broker.CHARLES_SCHWAB,
        markers=("Schwab Marker",),
    )
    text = make_text("TD Marker")

    first = BrokerDetector([td, unrelated]).detect(text)
    second = BrokerDetector([unrelated, td]).detect(text)

    assert first is Broker.TD_AMERITRADE
    assert second is Broker.TD_AMERITRADE
