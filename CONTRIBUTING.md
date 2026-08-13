# Contributing to brokerage-statements

Thank you for your interest in contributing to `brokerage-statements`.

Contributions are welcome, including support for additional statement layouts, bug fixes, documentation improvements, tests, reconciliation improvements, and focused feature proposals.

`brokerage-statements` is designed to provide deterministic extraction of brokerage statements into broker-neutral domain objects. Contributions should preserve that separation and favor extensibility over increasingly complex monolithic parsers.

## Development Setup

Clone the repository:

```bash id="76dsao"
git clone https://github.com/fifoa-labs/brokerage-statements.git
cd brokerage-statements
```

Install the development environment:

```bash id="q2o5gh"
uv sync
```

This project uses `uv` for dependency and environment management.

## Development Commands

The repository provides a `Makefile` for common development tasks.

Run the test suite:

```bash id="n3n93g"
make test
```

Run formatting:

```bash id="7ag9of"
make format
```

Run linting:

```bash id="15zxcp"
make lint
```

Run static type checking:

```bash id="cfrjlh"
make typecheck
```

Run coverage validation:

```bash id="jqih4c"
make coverage
```

Before submitting a release-related change, run the complete validation suite:

```bash id="8w33vi"
make release-check
```

All checks should pass before a pull request is submitted.

## Architecture

The package separates statement-specific extraction from broker-neutral financial concepts.

Conceptually:

```text id="8s5cxr"
Brokerage statement
        ↓
Text extraction
        ↓
Processor selection
        ↓
Statement-specific processor
        ↓
Broker-neutral domain objects
        ↓
Reconciliation / downstream consumers
```

The domain layer should not depend on the details of a particular PDF layout, extraction library, application framework, database, or accounting system.

Processors translate external statement formats into the package's domain model.

Keep that boundary clear.

## Broker-Neutral Domain

Types in the domain layer should describe financial concepts rather than document layouts.

Examples include concepts such as:

* Statements
* Statement periods
* Securities
* Positions
* Trades
* Income
* Fees
* Cash transfers
* Security transfers
* Corporate actions
* Option expirations
* Source evidence

Avoid adding broker-specific fields to shared domain objects merely because one statement format exposes additional information.

When broker-specific evidence needs to be retained, prefer appropriate evidence or processor-level structures rather than contaminating the common domain model.

## Processor Design

Statement processors should be focused and independently testable.

A processor should recognize and parse a specific statement format or compatible family of formats.

Do not assume that every historical or future statement from a brokerage uses the same layout.

When a new statement layout differs materially from an existing one, prefer adding a new processor or focused parsing strategy rather than continually expanding an existing processor with unrelated conditionals.

For example, if an existing processor reliably handles layouts A through E but layout F differs significantly, adding support for F should not jeopardize A through E.

Existing known-good statement behavior is a compatibility surface.

## Processor Selection

Processor selection must remain deterministic.

For a given statement, processor discovery should produce an unambiguous result.

Processors should positively identify the formats they support rather than relying on broad guesses.

Avoid changes that cause multiple processors to claim the same input unless the registry explicitly defines a deterministic and well-tested resolution mechanism.

Unknown formats should fail clearly rather than silently being interpreted by an incompatible processor.

## Parsing Philosophy

Parsing should favor correctness over permissiveness.

Do not silently invent missing financial information or reinterpret unknown activity merely to make a statement parse successfully.

When information cannot be interpreted safely, failing clearly is generally preferable to producing incorrect financial data.

Parser behavior should be:

* Deterministic
* Reproducible
* Explicit
* Testable
* Conservative with ambiguous input

A successfully parsed statement should mean substantially more than "no exception was raised."

## Financial Values

Financial arithmetic must avoid binary floating-point values.

Use `Decimal` and the project's existing decimal conversion utilities for monetary amounts, quantities, prices, fees, and other financial values where exact decimal behavior is required.

Do not introduce `float` into financial domain calculations.

Preserve the precision provided by the source whenever practical.

## Source Evidence

Parsed information should retain sufficient source evidence to explain where important values originated.

When extending extraction behavior, preserve or improve traceability rather than discarding useful source context.

This is particularly important for financial data because downstream consumers may need to diagnose discrepancies or verify reconstructed activity.

## Reconciliation

Reconciliation is a correctness mechanism, not merely informational output.

Where the source statement provides totals, balances, positions, or other independently verifiable information, processors and reconciliation components should use that information when appropriate to detect extraction errors.

Do not weaken reconciliation simply to allow a problematic fixture to pass.

If reconciliation reveals a legitimate unsupported statement condition, improve the parser or explicitly model the condition.

## Compatibility

Changes should preserve the Python versions supported by the project.

The authoritative compatibility information is maintained in `pyproject.toml` and the CI configuration.

Do not introduce dependencies on newer Python features without updating the declared compatibility policy and CI matrix.

## Dependencies

Keep runtime dependencies deliberate and minimal.

New dependencies should only be introduced when they provide substantial value that cannot reasonably be implemented using Python or existing project dependencies.

Parsing dependencies should not leak unnecessarily into the domain layer.

Please discuss significant new runtime dependencies before submitting a pull request that introduces them.

## Code Quality

Contributions should:

* Follow the existing project structure and conventions
* Include precise type annotations
* Pass Ruff formatting and linting
* Pass mypy type checking
* Preserve immutable domain models where applicable
* Preserve deterministic behavior
* Avoid unnecessary abstractions
* Keep public APIs intentional
* Maintain separation between processors and the domain

Prefer small, focused modules over increasingly large parser implementations.

## Tests

Behavior changes should include tests.

Bug fixes should normally include a regression test demonstrating the problem being fixed.

New processors or statement-layout support should include focused tests for:

* Recognition
* Extraction
* Domain conversion
* Important edge cases
* Expected failures
* Interactions with processor selection

Existing processor tests must continue to pass.

The project maintains full statement and branch coverage. Contributions should preserve that standard.

Do not add meaningless tests solely to satisfy a coverage percentage. Tests should verify useful behavior and important branches.

## Statement Fixtures

Do not commit customer statements, personal brokerage statements, account numbers, personally identifiable information, or other sensitive financial documents to the repository.

Tests should use synthetic fixtures specifically created for the project.

Synthetic fixtures should contain only the minimum information necessary to exercise the behavior being tested.

When reproducing a bug discovered in a real statement, create a sanitized synthetic fixture that reproduces the relevant structure without retaining private information.

## Public API

Treat additions to the public API carefully.

Implementation details should remain internal unless downstream applications have a clear reason to depend on them.

If a new class, function, enum, or protocol is intended to be public, export it consistently through the project's established public API and add appropriate public-import tests.

## Documentation

Changes to public behavior should include corresponding documentation updates.

New processor support should clearly document the supported brokerage and statement format where appropriate without implying support for layouts that have not been tested.

Avoid broad compatibility claims based on a small number of fixtures.

## Pull Requests

Keep pull requests focused.

A pull request should ideally address one statement format, bug, feature, refactor, or documentation concern.

Before submitting a pull request:

1. Update your branch from `main`.
2. Run formatting.
3. Run linting.
4. Run type checking.
5. Run the complete test suite.
6. Confirm coverage remains at the required level.
7. Update documentation when public behavior changes.
8. Review your diff for unrelated changes.

Please provide a clear pull request description explaining:

* What changed
* Why the change is needed
* Which statement formats or processors are affected
* Any important design decisions
* How the change was tested

Large architectural changes should generally be discussed before substantial implementation work begins.

## Backward Compatibility

Existing successfully parsed statement formats should continue to behave consistently.

A fix for one statement layout should not casually alter the interpretation of unrelated layouts.

If a contribution intentionally changes existing parsing behavior, explain the compatibility impact and reasoning in the pull request.

## Security Issues

Please do not report security vulnerabilities through public issues or pull requests.

Follow the instructions in `SECURITY.md` for responsible security reporting.

## Code of Conduct

Participation in this project is governed by the repository's `CODE_OF_CONDUCT.md`.

By participating, you are expected to follow those guidelines.

## License

By contributing to `brokerage-statements`, you agree that your contributions will be licensed under the same license as the project.

Thank you for helping improve `brokerage-statements`.
