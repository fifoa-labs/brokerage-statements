"""
tests/domain/test_evidence.py

Tests for brokerage statement source and evidence models.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from brokerage_statements.domain import SourceEvidence, StatementSource


def test_statement_source_preserves_identity() -> None:
    """Statement sources should preserve path and digest."""
    source = StatementSource(
        path=Path("statement.pdf"),
        sha256="abc123",
    )

    assert source.path == Path("statement.pdf")
    assert source.sha256 == "abc123"


def test_statement_source_rejects_empty_sha256() -> None:
    """Statement sources should require a digest."""
    with pytest.raises(ValueError, match="sha256 must not be empty"):
        StatementSource(
            path=Path("statement.pdf"),
            sha256="",
        )


def test_source_evidence_preserves_provenance() -> None:
    """Source evidence should retain parser provenance."""
    source = StatementSource(
        path=Path("statement.pdf"),
        sha256="abc123",
    )

    evidence = SourceEvidence(
        source=source,
        page=4,
        section="Account Activity",
        raw_text="BUY 10 XYZ",
        processor="tdameritrade.monthly_2020",
        reference="ABC123",
        sequence=7,
    )

    assert evidence.source is source
    assert evidence.page == 4
    assert evidence.section == "Account Activity"
    assert evidence.raw_text == "BUY 10 XYZ"
    assert evidence.processor == "tdameritrade.monthly_2020"
    assert evidence.reference == "ABC123"
    assert evidence.sequence == 7


@pytest.mark.parametrize(
    "page",
    [
        0,
        -1,
    ],
)
def test_source_evidence_rejects_invalid_page(page: int) -> None:
    """Evidence pages should use one-based numbering."""
    source = StatementSource(
        path=Path("statement.pdf"),
        sha256="abc123",
    )

    with pytest.raises(ValueError, match="page must be at least 1"):
        SourceEvidence(
            source=source,
            page=page,
        )


def test_source_evidence_rejects_negative_sequence() -> None:
    """Evidence sequence numbers should not be negative."""
    source = StatementSource(
        path=Path("statement.pdf"),
        sha256="abc123",
    )

    with pytest.raises(
        ValueError,
        match="sequence must not be negative",
    ):
        SourceEvidence(
            source=source,
            sequence=-1,
        )
