"""
src/brokerage_statements/text/reader.py

Contract for extracting normalized text from brokerage statements.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from brokerage_statements.domain import StatementSource

    from .models import StatementText


class StatementTextReader(Protocol):
    """Contract implemented by statement text readers."""

    def read(
        self,
        source: StatementSource,
    ) -> StatementText:
        """Extract normalized text from a statement source."""
        ...
