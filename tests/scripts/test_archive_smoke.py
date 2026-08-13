"""
tests/scripts/test_archive_smoke.py

Tests for private archive smoke-runner discovery and composition.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from brokerage_statements.domain import Broker
from scripts import archive_smoke

if TYPE_CHECKING:
    from pathlib import Path

    from brokerage_statements.processors.base import StatementProcessor


def test_build_broker_detector_registers_all_supported_brokers() -> None:
    """Smoke composition should register every supported broker."""
    detector = archive_smoke.build_broker_detector()

    brokers = {signature.broker for signature in detector.signatures}

    assert brokers == {
        Broker.TD_AMERITRADE,
        Broker.CHARLES_SCHWAB,
    }


def test_build_processor_registry_registers_broker_processors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Smoke composition should register all implemented processors."""
    captured: list[StatementProcessor] = []

    class FakeRegistry:
        """Capture processors supplied by the smoke composition root."""

        def __init__(
            self,
            processors: list[StatementProcessor],
        ) -> None:
            captured.extend(processors)

    monkeypatch.setattr(
        archive_smoke,
        "ProcessorRegistry",
        FakeRegistry,
    )

    archive_smoke.build_processor_registry()

    names = [processor.name for processor in captured]
    brokers = [processor.broker for processor in captured]

    assert names == [
        "tdameritrade.transition_2023",
        "tdameritrade.monthly_2020",
        "charlesschwab.monthly_2023",
    ]
    assert brokers == [
        Broker.TD_AMERITRADE,
        Broker.TD_AMERITRADE,
        Broker.CHARLES_SCHWAB,
    ]


def test_discover_statements_returns_single_pdf_file(
    tmp_path: Path,
) -> None:
    """A PDF source file should be returned directly."""
    source = tmp_path / "statement.pdf"
    source.touch()

    statements = archive_smoke.discover_statements(source)

    assert statements == (source,)


def test_discover_statements_recurses_and_sorts_pdfs(
    tmp_path: Path,
) -> None:
    """Directory discovery should recursively return sorted PDFs only."""
    nested = tmp_path / "nested"
    nested.mkdir()

    later = tmp_path / "z-statement.PDF"
    earlier = tmp_path / "a-statement.pdf"
    nested_pdf = nested / "m-statement.PdF"
    ignored = tmp_path / "notes.txt"

    later.touch()
    earlier.touch()
    nested_pdf.touch()
    ignored.touch()

    statements = archive_smoke.discover_statements(tmp_path)

    assert statements == tuple(
        sorted(
            (
                earlier,
                nested_pdf,
                later,
            )
        )
    )


def test_discover_statements_rejects_missing_source(
    tmp_path: Path,
) -> None:
    """Missing archive sources should fail explicitly."""
    source = tmp_path / "missing"

    with pytest.raises(
        ValueError,
        match="statement source does not exist",
    ):
        archive_smoke.discover_statements(source)


def test_run_archive_smoke_stops_after_first_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Default smoke execution should stop at the first failure."""
    first = tmp_path / "first.pdf"
    second = tmp_path / "second.pdf"

    calls: list[Path] = []

    def fake_parse_statement(
        source: Path,
        **kwargs: Any,
    ) -> object:
        del kwargs
        calls.append(source)
        msg = "parse failed"
        raise RuntimeError(msg)

    monkeypatch.setattr(
        archive_smoke,
        "parse_statement",
        fake_parse_statement,
    )

    failures = archive_smoke.run_archive_smoke(
        (first, second),
        continue_on_error=False,
        show_traceback=False,
    )

    output = capsys.readouterr().out

    assert failures == 1
    assert calls == [first]
    assert "[01/02] FAIL first.pdf" in output
    assert "RuntimeError: parse failed" in output


def test_run_archive_smoke_can_continue_after_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Continue mode should attempt every requested statement."""
    first = tmp_path / "first.pdf"
    second = tmp_path / "second.pdf"

    calls: list[Path] = []

    def fake_parse_statement(
        source: Path,
        **kwargs: Any,
    ) -> object:
        del kwargs
        calls.append(source)
        msg = "parse failed"
        raise RuntimeError(msg)

    monkeypatch.setattr(
        archive_smoke,
        "parse_statement",
        fake_parse_statement,
    )

    failures = archive_smoke.run_archive_smoke(
        (first, second),
        continue_on_error=True,
        show_traceback=False,
    )

    assert failures == 2
    assert calls == [
        first,
        second,
    ]
