# brokerage-statements

[![PyPI version](https://img.shields.io/pypi/v/brokerage-statements.svg)](https://pypi.org/project/brokerage-statements/)
[![Python versions](https://img.shields.io/pypi/pyversions/brokerage-statements.svg)](https://pypi.org/project/brokerage-statements/)
[![CI](https://github.com/fifoa-labs/brokerage-statements/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/fifoa-labs/brokerage-statements/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/fifoa-labs/brokerage-statements/branch/main/graph/badge.svg)](https://codecov.io/gh/fifoa-labs/brokerage-statements)
[![License](https://img.shields.io/pypi/l/brokerage-statements.svg)](https://github.com/fifoa-labs/brokerage-statements/blob/main/LICENSE)

A deterministic Python library for parsing, normalizing, and validating
brokerage statements.

`brokerage-statements` converts supported brokerage statements into normalized,
broker-neutral Python objects while preserving the source evidence needed to
audit how each result was produced.

The library is built around isolated statement processors. Each processor owns
a known statement format or revision, allowing support for new statement
variants to be added without destabilizing processors already proven against
historical statements.

The project emphasizes strict, deterministic behavior. Unsupported statement
formats, ambiguous broker or processor matches, unknown financial activity, and
invalid processor output fail explicitly rather than being silently ignored or
guessed.

TD Ameritrade monthly statement support is currently under active development.
The first real TD Ameritrade monthly grammar is implemented and parses the
March 2020 statement format end-to-end, including statement identity, reported
positions, settled activity, regulatory fees, external cash transfers, internal
cash movements, security transfers, and trades pending settlement.

Charles Schwab statement support is planned next and will use the same
broker-detection and isolated-processor architecture.

It intentionally focuses on statement processing and normalization. It is not
a portfolio manager, brokerage API, trading system, tax engine, or
Beancount-specific importer.

* **PyPI:** https://pypi.org/project/brokerage-statements/
* **Source:** https://github.com/fifoa-labs/brokerage-statements
* **License:** MIT

## Current Status

The package currently includes:

* Page-aware PDF text extraction
* SHA-256 statement source identity
* Deterministic broker detection
* Broker-scoped processor selection
* Strict processor ambiguity detection
* Broker-neutral security, position, and event domain models
* Source evidence attached to normalized results
* TD Ameritrade monthly statement identity parsing
* TD Ameritrade account-position parsing
* TD Ameritrade settled trade parsing
* TD Ameritrade regulatory fee parsing
* TD Ameritrade external cash-transfer parsing
* TD Ameritrade internal cash-movement handling
* TD Ameritrade security-transfer parsing
* TD Ameritrade pending-trade parsing
* Private archive inspection and smoke-test tooling
* Fully typed public package
* 100% branch test coverage

Support is expanded chronologically against real historical statements. New
statement grammars are added only when the existing processor cannot safely
handle a format, rather than broadening old processors with speculative
fallback behavior.

## Design Goals

* Deterministic broker detection and processor selection
* Strict failure instead of silent guessing or skipped activity
* Broker-neutral normalized domain objects
* Exact decimal arithmetic for financial values and quantities
* Traceable source evidence for normalized results
* Isolated processors for distinct statement formats and revisions
* Regression-safe support for new statement variants
* Real-statement validation against a private historical corpus
* Small, stable public APIs

## Processing Model

The package follows a staged processing pipeline:

```text
statement PDF
    ↓
page-aware text extraction
    ↓
broker detection
    ↓
broker-scoped processor selection
    ↓
statement identity and section discovery
    ↓
normalized positions and events
    ↓
strict validation
    ↓
ParsedStatement
```

Broker detection and statement-format detection are intentionally separate.
Once a brokerage institution is identified, only processors belonging to that
broker are allowed to compete for the statement.

## Installation

```bash
pip install brokerage-statements
```

Or with `uv`:

```bash
uv add brokerage-statements
```
