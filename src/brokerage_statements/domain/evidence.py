"""
src/brokerage_statements/domain/evidence.py

Source identity and evidence models for brokerage statement parsing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(frozen=True, slots=True)
class StatementSource:
    """Identify the original brokerage statement source."""

    path: Path
    sha256: str

    def __post_init__(self) -> None:
        """Validate source identity fields."""
        if not self.sha256:
            msg = "sha256 must not be empty."
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class SourceEvidence:
    """Preserve traceable source evidence for normalized data."""

    source: StatementSource
    page: int | None = None
    section: str | None = None
    raw_text: str | None = None
    processor: str | None = None
    reference: str | None = None
    sequence: int | None = None

    def __post_init__(self) -> None:
        """Validate evidence coordinates."""
        if self.page is not None and self.page < 1:
            msg = "page must be at least 1."
            raise ValueError(msg)

        if self.sequence is not None and self.sequence < 0:
            msg = "sequence must not be negative."
            raise ValueError(msg)
