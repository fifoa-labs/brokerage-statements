"""
src/brokerage_statements/api.py

Public orchestration for brokerage statement parsing.
"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import TYPE_CHECKING

from brokerage_statements.domain import (
    Broker,
    ParsedStatement,
    StatementSource,
)
from brokerage_statements.exceptions import (
    InvalidProcessorResultError,
    StatementSourceError,
)

if TYPE_CHECKING:
    from brokerage_statements.processors import (
        BrokerDetector,
        ProcessorRegistry,
    )
    from brokerage_statements.text import StatementTextReader


def parse_statement(
    source: str | Path,
    *,
    text_reader: StatementTextReader,
    broker_detector: BrokerDetector,
    registry: ProcessorRegistry,
) -> ParsedStatement:
    """Parse one brokerage statement into normalized domain data."""
    statement_source = _build_statement_source(source)
    text = text_reader.read(statement_source)
    broker = broker_detector.detect(text)

    processor = registry.select(
        text,
        broker=broker,
    )

    statement = processor.parse(
        statement_source,
        text,
    )

    _validate_processor_result(
        statement=statement,
        source=statement_source,
        processor_name=processor.name,
        processor_broker=processor.broker,
    )

    return statement


def _build_statement_source(
    source: str | Path,
) -> StatementSource:
    """Create source identity with a deterministic SHA-256 digest."""
    path = Path(source)

    try:
        digest = _sha256_file(path)
    except OSError as exc:
        msg = f"Could not read statement source: {path}."
        raise StatementSourceError(msg) from exc

    return StatementSource(
        path=path,
        sha256=digest,
    )


def _sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of a statement source."""
    digest = sha256()

    with path.open("rb") as source_file:
        while chunk := source_file.read(1024 * 1024):
            digest.update(chunk)

    return digest.hexdigest()


def _validate_processor_result(
    *,
    statement: ParsedStatement,
    source: StatementSource,
    processor_name: str,
    processor_broker: Broker,
) -> None:
    """Require processor output to match its parsing context."""
    if statement.source != source:
        msg = (
            f"Processor {processor_name!r} returned a statement "
            "for a different source."
        )
        raise InvalidProcessorResultError(msg)

    if statement.broker is not processor_broker:
        msg = (
            f"Processor {processor_name!r} returned broker "
            f"{statement.broker!r}, expected {processor_broker!r}."
        )
        raise InvalidProcessorResultError(msg)

    if statement.processor_name != processor_name:
        msg = (
            f"Processor {processor_name!r} returned processor name "
            f"{statement.processor_name!r}."
        )
        raise InvalidProcessorResultError(msg)
