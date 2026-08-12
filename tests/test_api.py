"""
tests/test_api.py

Tests for public brokerage statement parsing orchestration.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from hashlib import sha256
from pathlib import Path

import pytest

from brokerage_statements import parse_statement
from brokerage_statements.domain import (
    Broker,
    ParsedStatement,
    StatementPeriod,
    StatementSource,
)
from brokerage_statements.exceptions import (
    InvalidProcessorResultError,
    StatementSourceError,
)
from brokerage_statements.processors import (
    ProcessorMatch,
    ProcessorRegistry,
)
from brokerage_statements.text import (
    StatementPage,
    StatementText,
)


@dataclass(slots=True)
class FakeReader:
    """Return configured text while recording the received source."""

    text: StatementText
    received_source: StatementSource | None = None

    def read(
        self,
        source: StatementSource,
    ) -> StatementText:
        """Return configured statement text."""
        self.received_source = source
        return self.text


@dataclass(slots=True)
class FakeProcessor:
    """Minimal processor for orchestration tests."""

    name: str
    broker: Broker
    priority: int
    result: ProcessorMatch
    returned_source: StatementSource | None = None
    returned_broker: Broker | None = None
    received_source: StatementSource | None = None
    received_text: StatementText | None = None

    def match(
        self,
        text: StatementText,
    ) -> ProcessorMatch:
        """Return configured processor matching metadata."""
        del text
        return self.result

    def parse(
        self,
        source: StatementSource,
        text: StatementText,
    ) -> ParsedStatement:
        """Return a normalized statement for orchestration testing."""
        self.received_source = source
        self.received_text = text

        statement_source = (
            source if self.returned_source is None else self.returned_source
        )
        statement_broker = (
            self.broker
            if self.returned_broker is None
            else self.returned_broker
        )

        return ParsedStatement(
            source=statement_source,
            broker=statement_broker,
            period=StatementPeriod(
                start=date(2026, 1, 1),
                end=date(2026, 1, 31),
            ),
        )


def make_text() -> StatementText:
    """Return representative statement text."""
    return StatementText(
        pages=(
            StatementPage(
                number=1,
                text="Brokerage statement",
            ),
        ),
    )


def make_processor() -> FakeProcessor:
    """Return a processor that matches the test statement."""
    return FakeProcessor(
        name="test.processor",
        broker=Broker.CHARLES_SCHWAB,
        priority=10,
        result=ProcessorMatch(
            matched=True,
            confidence=100,
            reason="Test statement matched.",
        ),
    )


def test_parse_statement_returns_processor_result(
    tmp_path: Path,
) -> None:
    """Parsing should return the selected processor result."""
    path = tmp_path / "statement.pdf"
    path.write_bytes(b"brokerage statement")

    reader = FakeReader(text=make_text())
    processor = make_processor()

    statement = parse_statement(
        path,
        text_reader=reader,
        registry=ProcessorRegistry([processor]),
    )

    assert statement.broker is Broker.CHARLES_SCHWAB
    assert statement.period == StatementPeriod(
        start=date(2026, 1, 1),
        end=date(2026, 1, 31),
    )


def test_parse_statement_accepts_string_path(
    tmp_path: Path,
) -> None:
    """Public parsing should accept string filesystem paths."""
    path = tmp_path / "statement.pdf"
    path.write_bytes(b"brokerage statement")

    statement = parse_statement(
        str(path),
        text_reader=FakeReader(text=make_text()),
        registry=ProcessorRegistry([make_processor()]),
    )

    assert statement.source.path == path


def test_parse_statement_builds_sha256_source_identity(
    tmp_path: Path,
) -> None:
    """Statement sources should include the exact file digest."""
    contents = b"brokerage statement contents"
    path = tmp_path / "statement.pdf"
    path.write_bytes(contents)

    statement = parse_statement(
        path,
        text_reader=FakeReader(text=make_text()),
        registry=ProcessorRegistry([make_processor()]),
    )

    assert statement.source.sha256 == sha256(contents).hexdigest()


def test_parse_statement_passes_source_to_reader(
    tmp_path: Path,
) -> None:
    """Text readers should receive normalized source identity."""
    contents = b"statement"
    path = tmp_path / "statement.pdf"
    path.write_bytes(contents)

    reader = FakeReader(text=make_text())

    parse_statement(
        path,
        text_reader=reader,
        registry=ProcessorRegistry([make_processor()]),
    )

    assert reader.received_source is not None
    assert reader.received_source.path == path
    assert (
        reader.received_source.sha256
        == sha256(
            contents,
        ).hexdigest()
    )


def test_parse_statement_passes_source_and_text_to_processor(
    tmp_path: Path,
) -> None:
    """Selected processors should receive source and text."""
    path = tmp_path / "statement.pdf"
    path.write_bytes(b"statement")

    text = make_text()
    reader = FakeReader(text=text)
    processor = make_processor()

    parse_statement(
        path,
        text_reader=reader,
        registry=ProcessorRegistry([processor]),
    )

    assert processor.received_source is reader.received_source
    assert processor.received_text is text


def test_parse_statement_rejects_unreadable_source(
    tmp_path: Path,
) -> None:
    """Unreadable statement sources should fail explicitly."""
    path = tmp_path / "missing.pdf"

    with pytest.raises(
        StatementSourceError,
        match="Could not read statement source",
    ):
        parse_statement(
            path,
            text_reader=FakeReader(text=make_text()),
            registry=ProcessorRegistry([make_processor()]),
        )


def test_parse_statement_rejects_wrong_processor_source(
    tmp_path: Path,
) -> None:
    """Processor output should retain parsed source identity."""
    path = tmp_path / "statement.pdf"
    path.write_bytes(b"statement")

    processor = make_processor()
    processor.returned_source = StatementSource(
        path=Path("different.pdf"),
        sha256="different",
    )

    with pytest.raises(
        InvalidProcessorResultError,
        match="returned a statement for a different source",
    ):
        parse_statement(
            path,
            text_reader=FakeReader(text=make_text()),
            registry=ProcessorRegistry([processor]),
        )


def test_parse_statement_rejects_wrong_processor_broker(
    tmp_path: Path,
) -> None:
    """Processor output should retain processor broker identity."""
    path = tmp_path / "statement.pdf"
    path.write_bytes(b"statement")

    processor = make_processor()
    processor.returned_broker = Broker.TD_AMERITRADE

    with pytest.raises(
        InvalidProcessorResultError,
        match="returned broker",
    ):
        parse_statement(
            path,
            text_reader=FakeReader(text=make_text()),
            registry=ProcessorRegistry([processor]),
        )
