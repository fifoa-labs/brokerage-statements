"""
tests/text/test_pdf.py

Tests for PDF-backed brokerage statement text extraction.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from brokerage_statements.domain import StatementSource
from brokerage_statements.exceptions import StatementSourceError
from brokerage_statements.text import PdfStatementTextReader


def make_source() -> StatementSource:
    """Return reusable PDF source identity."""
    return StatementSource(
        path=Path("statement.pdf"),
        sha256="abc123",
    )


def test_pdf_reader_preserves_page_order() -> None:
    """PDF extraction should preserve one-based page ordering."""
    first = MagicMock()
    first.extract_text.return_value = "Page one"

    second = MagicMock()
    second.extract_text.return_value = "Page two"

    pdf = MagicMock()
    pdf.pages = [first, second]

    manager = MagicMock()
    manager.__enter__.return_value = pdf

    with patch(
        "brokerage_statements.text.pdf.pdfplumber.open",
        return_value=manager,
    ):
        text = PdfStatementTextReader().read(
            make_source(),
        )

    assert len(text.pages) == 2
    assert text.pages[0].number == 1
    assert text.pages[0].text == "Page one"
    assert text.pages[1].number == 2
    assert text.pages[1].text == "Page two"


def test_pdf_reader_preserves_blank_page() -> None:
    """Blank PDF pages should remain explicit statement pages."""
    page = MagicMock()
    page.extract_text.return_value = None

    pdf = MagicMock()
    pdf.pages = [page]

    manager = MagicMock()
    manager.__enter__.return_value = pdf

    with patch(
        "brokerage_statements.text.pdf.pdfplumber.open",
        return_value=manager,
    ):
        text = PdfStatementTextReader().read(
            make_source(),
        )

    assert len(text.pages) == 1
    assert text.pages[0].number == 1
    assert text.pages[0].text == ""


def test_pdf_reader_allows_empty_pdf() -> None:
    """An empty PDF should produce empty statement text."""
    pdf = MagicMock()
    pdf.pages = []

    manager = MagicMock()
    manager.__enter__.return_value = pdf

    with patch(
        "brokerage_statements.text.pdf.pdfplumber.open",
        return_value=manager,
    ):
        text = PdfStatementTextReader().read(
            make_source(),
        )

    assert text.pages == ()
    assert text.text == ""


def test_pdf_reader_wraps_os_error() -> None:
    """Filesystem PDF failures should become package source errors."""
    with (
        patch(
            "brokerage_statements.text.pdf.pdfplumber.open",
            side_effect=OSError("cannot open"),
        ),
        pytest.raises(
            StatementSourceError,
            match="Could not read PDF statement source",
        ),
    ):
        PdfStatementTextReader().read(
            make_source(),
        )
