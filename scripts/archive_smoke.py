"""
scripts/archive_smoke.py

Run real private brokerage statement PDFs through the public parsing pipeline.
"""

from __future__ import annotations

import argparse
import traceback
from collections import Counter
from pathlib import Path
from typing import TYPE_CHECKING

from brokerage_statements import parse_statement
from brokerage_statements.processors import (
    BrokerDetector,
    ProcessorRegistry,
)
from brokerage_statements.processors.charlesschwab import (
    BROKER_SIGNATURES as SCHWAB_BROKER_SIGNATURES,
)
from brokerage_statements.processors.charlesschwab import (
    Monthly2023Processor as SchwabMonthly2023Processor,
)
from brokerage_statements.processors.tdameritrade import (
    BROKER_SIGNATURES as TDA_BROKER_SIGNATURES,
)
from brokerage_statements.processors.tdameritrade import (
    Monthly2020Processor as TdaMonthly2020Processor,
)
from brokerage_statements.processors.tdameritrade import (
    Transition2023Processor as TdaTransition2023Processor,
)
from brokerage_statements.text import PdfStatementTextReader

if TYPE_CHECKING:
    from collections.abc import Sequence

    from brokerage_statements.domain import ParsedStatement


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Run private brokerage statement PDFs through "
            "brokerage-statements."
        ),
    )
    parser.add_argument(
        "source",
        type=Path,
        help="PDF file or directory containing statement PDFs.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Process only the first N discovered statements.",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue processing after a statement fails.",
    )
    parser.add_argument(
        "--traceback",
        action="store_true",
        help="Show Python tracebacks for failures.",
    )
    return parser


def discover_statements(
    source: Path,
) -> tuple[Path, ...]:
    """Return statement PDFs in deterministic path order."""
    if source.is_file():
        return (source,)

    if not source.is_dir():
        msg = f"statement source does not exist: {source}"
        raise ValueError(msg)

    return tuple(
        sorted(
            path
            for path in source.rglob("*")
            if path.is_file() and path.suffix.casefold() == ".pdf"
        )
    )


def build_broker_detector() -> BrokerDetector:
    """Return detector configured with implemented broker signatures."""
    return BrokerDetector(
        (
            *TDA_BROKER_SIGNATURES,
            *SCHWAB_BROKER_SIGNATURES,
        )
    )


def build_processor_registry() -> ProcessorRegistry:
    """Return registry containing implemented statement processors."""
    return ProcessorRegistry(
        [
            TdaTransition2023Processor(),
            TdaMonthly2020Processor(),
            SchwabMonthly2023Processor(),
        ]
    )


def run_archive_smoke(
    statements: Sequence[Path],
    *,
    continue_on_error: bool,
    show_traceback: bool,
) -> int:
    """Parse statements and return the number of failures."""
    reader = PdfStatementTextReader()
    detector = build_broker_detector()
    registry = build_processor_registry()

    failures = 0
    total = len(statements)

    for index, path in enumerate(
        statements,
        start=1,
    ):
        label = f"[{index:02d}/{total:02d}]"

        try:
            statement = parse_statement(
                path,
                text_reader=reader,
                broker_detector=detector,
                registry=registry,
            )
        except Exception as exc:  # noqa: BLE001
            failures += 1

            print(f"{label} FAIL {path.name}")  # noqa: T201
            print(  # noqa: T201
                f"         {type(exc).__name__}: {exc}",
            )

            if show_traceback:
                traceback.print_exc()

            if not continue_on_error:
                break

            continue

        _print_success(
            label,
            path,
            statement,
        )

    return failures


def _print_success(
    label: str,
    path: Path,
    statement: ParsedStatement,
) -> None:
    """Print a concise normalized statement summary."""
    event_counts = Counter(type(event).__name__ for event in statement.events)

    event_summary = ", ".join(
        f"{name}={count}" for name, count in sorted(event_counts.items())
    )

    if not event_summary:
        event_summary = "none"

    print(f"{label} PASS {path.name}")  # noqa: T201
    print(  # noqa: T201
        "         "
        f"broker={statement.broker.value} "
        f"processor={statement.processor_name}",
    )
    print(  # noqa: T201
        "         "
        f"period={statement.period.start.isoformat()}"
        ".."
        f"{statement.period.end.isoformat()} "
        f"account={statement.account_id}",
    )
    print(  # noqa: T201
        "         "
        f"positions={len(statement.positions)} "
        f"events={len(statement.events)} "
        f"({event_summary})",
    )


def main() -> None:
    """Run archive smoke validation."""
    parser = build_parser()
    args = parser.parse_args()

    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be at least 1")

    try:
        statements = discover_statements(
            args.source,
        )
    except ValueError as exc:
        parser.error(str(exc))

    if args.limit is not None:
        statements = statements[: args.limit]

    if not statements:
        parser.error(f"no PDF statements found under: {args.source}")

    failures = run_archive_smoke(
        statements,
        continue_on_error=args.continue_on_error,
        show_traceback=args.traceback,
    )

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
