"""
src/brokerage_statements/text/__init__.py

Statement text models and extraction contracts.
"""

from __future__ import annotations

from .models import StatementPage, StatementText
from .pdf import PdfStatementTextReader
from .readers import StatementTextReader

__all__ = [
    "PdfStatementTextReader",
    "StatementPage",
    "StatementText",
    "StatementTextReader",
]
