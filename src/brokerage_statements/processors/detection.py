"""
src/brokerage_statements/processors/detection.py

Deterministic brokerage institution detection.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from brokerage_statements.exceptions import (
    AmbiguousBrokerError,
    UnsupportedBrokerError,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

    from brokerage_statements.domain import Broker
    from brokerage_statements.text import StatementText


@dataclass(frozen=True, slots=True)
class BrokerSignature:
    """Describe one strong document signature for a broker."""

    name: str
    broker: Broker
    markers: tuple[str, ...]

    def __post_init__(self) -> None:
        """Validate and normalize signature metadata."""
        name = self.name.strip()

        if not name:
            msg = "broker signature name must not be empty."
            raise ValueError(msg)

        if not self.markers:
            msg = "broker signature markers must not be empty."
            raise ValueError(msg)

        markers = tuple(marker.strip() for marker in self.markers)

        if any(not marker for marker in markers):
            msg = "broker signature markers must not contain empty values."
            raise ValueError(msg)

        object.__setattr__(self, "name", name)
        object.__setattr__(self, "markers", markers)

    def matches(self, text: StatementText) -> bool:
        """Return whether all required markers occur in statement text."""
        statement_text = text.text.casefold()

        return all(
            marker.casefold() in statement_text for marker in self.markers
        )


class BrokerDetector:
    """Detect exactly one brokerage institution from statement text."""

    def __init__(
        self,
        signatures: Iterable[BrokerSignature] = (),
    ) -> None:
        """Create a detector from immutable broker signatures."""
        self._signatures = tuple(signatures)
        self._validate_unique_names()

    @property
    def signatures(self) -> tuple[BrokerSignature, ...]:
        """Return configured broker signatures."""
        return self._signatures

    def detect(self, text: StatementText) -> Broker:
        """Return the uniquely detected brokerage institution."""
        brokers = {
            signature.broker
            for signature in self._signatures
            if signature.matches(text)
        }

        if not brokers:
            msg = "No supported broker signature matched statement text."
            raise UnsupportedBrokerError(msg)

        if len(brokers) > 1:
            names = ", ".join(sorted(broker.value for broker in brokers))
            msg = (
                f"Multiple broker signatures matched statement text: {names}."
            )
            raise AmbiguousBrokerError(msg)

        return next(iter(brokers))

    def _validate_unique_names(self) -> None:
        """Require unique broker signature names."""
        names: set[str] = set()

        for signature in self._signatures:
            if signature.name in names:
                msg = (
                    "Broker signature names must be unique: "
                    f"{signature.name!r}."
                )
                raise ValueError(msg)

            names.add(signature.name)
