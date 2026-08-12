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
formats, ambiguous processor matches, unknown financial activity, and
unresolved security identities fail explicitly rather than being silently
ignored or guessed.

Initial brokerage support is being developed for TD Ameritrade and Charles
Schwab statements.

It intentionally focuses on statement processing and normalization. It is not
a portfolio manager, brokerage API, trading system, tax engine, or
Beancount-specific importer.

* **PyPI:** https://pypi.org/project/brokerage-statements/
* **Source:** https://github.com/fifoa-labs/brokerage-statements
* **License:** MIT

## Design Goals

* Deterministic parsing and processor selection
* Strict failure instead of silent guessing or skipped activity
* Broker-neutral normalized domain objects
* Exact decimal arithmetic for financial values and quantities
* Traceable source evidence for normalized results
* Isolated processors for distinct statement formats and revisions
* Regression-safe support for new statement variants
* Small, stable public APIs

## Installation

```bash
pip install brokerage-statements
```

Or with `uv`:

```bash
uv add brokerage-statements
```
