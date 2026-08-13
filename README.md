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
formats, ambiguous broker or processor matches, unknown financial activity,
unresolved security identities, and invalid processor output fail explicitly
rather than being silently ignored or guessed.

TD Ameritrade monthly statement support is currently under active development.
The first real TD Ameritrade monthly processor has been validated
chronologically against real historical statements from March through October
2020.

Charles Schwab statement support is planned next and will use the same
broker-detection, isolated-processor, and capability-extension architecture.

The package intentionally focuses on statement processing and normalization.
It is not a portfolio manager, brokerage API, trading system, tax engine, or
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
* Traceable source evidence attached to normalized results
* Exact `Decimal` handling for financial quantities and amounts
* TD Ameritrade monthly statement identity parsing
* TD Ameritrade account-position parsing
* TD Ameritrade settled equity trade parsing
* TD Ameritrade option trade parsing
* TD Ameritrade option expiration parsing
* TD Ameritrade regulatory fee parsing
* TD Ameritrade option commission/fee parsing
* TD Ameritrade external cash-transfer parsing
* TD Ameritrade internal cash-movement handling
* TD Ameritrade security-transfer parsing
* TD Ameritrade reverse-split activity handling
* TD Ameritrade cash-in-lieu parsing
* TD Ameritrade mandatory reorganization fee parsing
* TD Ameritrade pending-trade parsing
* CUSIP-to-symbol reference resolution for observed statement identifiers
* Private archive inspection and smoke-test tooling
* Fully typed public package
* 100% branch test coverage

Real TD Ameritrade archive coverage currently includes:

```text
2020-03  PASS
2020-04  PASS
2020-05  PASS
2020-06  PASS
2020-07  PASS
2020-08  PASS
2020-09  PASS
2020-10  PASS
```

Archive coverage is intentionally earned chronologically. A statement is not
considered supported merely because its processor matches. It must pass through
the real parsing pipeline without unsupported or ambiguous behavior.

## Design Goals

* Deterministic broker detection and processor selection
* Strict failure instead of silent guessing or skipped activity
* Broker-neutral normalized domain objects
* Exact decimal arithmetic for financial values and quantities
* Traceable source evidence for normalized results
* Isolated processors for distinct statement formats and revisions
* Focused capability modules for individual economic grammars
* Regression-safe support for new statement variants
* Real-statement validation against a private historical corpus
* Small, stable public APIs
* Proven historical processors remain stable as support expands

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
focused section/activity parsers
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

## Processor Architecture

A statement processor represents a known statement layout or revision.

For example:

```text
processors/
└── tdameritrade/
    ├── monthly_2020.py
    ├── identity.py
    ├── sections.py
    ├── positions.py
    ├── pending.py
    └── activity/
        ├── __init__.py
        ├── rows.py
        ├── trades.py
        ├── options.py
        ├── option_expirations.py
        ├── cash.py
        ├── income.py
        ├── transfers.py
        └── corporate_actions.py
```

`monthly_2020.py` is intentionally small. It owns the statement revision and
orchestrates focused parsing capabilities.

It should not become a large collection of transaction-specific regular
expressions.

The activity subsystem follows the same rule. Each economic grammar lives in a
focused module rather than accumulating inside one large parser.

## Extension Rule

This is the most important maintenance rule in the project.

When a new real statement fails, first determine **what changed**.

### Same statement format, new economic capability

If the statement structure is still the same but it exposes a new kind of
activity, add or extend a focused capability.

Examples:

```text
new option trade grammar
    → activity/options.py

option expiration
    → activity/option_expirations.py

reverse split or reorganization
    → activity/corporate_actions.py

new security identifier
    → reference/identifiers.py
```

Do not create a new statement processor merely because a new transaction type
appears.

### Same capability, new observed grammar variant

If an existing capability encounters another legitimate representation of the
same economic event, extend only that capability.

For example:

```text
September 2020:
Delivered - Other ... EXPIRATION

October 2020:
Received - Other ... EXPIRATION
```

Both represent option expiration.

The correct extension is therefore:

```text
activity/option_expirations.py
```

not:

```text
monthly_2020.py
```

and not a new statement processor.

### Materially different statement format or revision

If a later statement changes the document grammar substantially, such as:

* different section structure
* different identifying markers
* incompatible column layout
* materially different transaction grammar
* different statement revision that cannot be handled safely without
  destabilizing proven statements

then add a new processor.

Conceptually:

```text
monthly_2020.py        ← proven and retained
monthly_<revision>.py  ← new format
```

The processor registry should then select deterministically between them.

### Do not keep bending a proven processor

Once a processor has been proven against historical statements, treat that
behavior as locked.

Do not rewrite broad parsing rules merely to make a later file pass.

Instead ask:

```text
Is this a new identifier?
    → reference layer

Is this a new economic event?
    → focused capability module

Is this another representation of an existing event?
    → extend that capability

Is the actual statement format different?
    → new processor
```

This distinction is fundamental to the maintainability of the package.

## Specific Before Generic

Activity parsers are ordered from more specific grammars to more general ones.

For example:

```text
option trade
    before
generic equity trade

option expiration
    before
generic security transfer
```

A TD Ameritrade option expiration may visually appear as:

```text
Cash Delivered - Other
```

or:

```text
Cash Received - Other
```

but economically it is an option expiration, not an external security transfer.

The specific parser must therefore receive the row first.

The dispatcher in `activity/__init__.py` owns this precedence.

Individual capability modules should not need to know about unrelated
capabilities.

## Private Statement Corpus

Real brokerage statements used for development live under:

```text
private-data/statements/
├── tdameritrade/
└── charlesschwab/
```

These files are private development evidence and must not be committed or
distributed with the package.

The private corpus is used to validate real parsing behavior after unit tests
have proven individual grammar rules.

## Inspecting a Statement

When a real statement fails, inspect the extracted PDF text before changing
production code.

Inspect an entire statement:

```bash
make inspect-statement \
    file="private-data/statements/tdameritrade/TDA - Brokerage Statement_2020-10-31_484.PDF"
```

Inspect one page:

```bash
make inspect-statement \
    file="private-data/statements/tdameritrade/TDA - Brokerage Statement_2020-10-31_484.PDF" \
    page=5
```

Limit displayed text when useful:

```bash
make inspect-statement \
    file="private-data/statements/tdameritrade/TDA - Brokerage Statement_2020-10-31_484.PDF" \
    head=2000
```

The inspection command shows the actual text produced by the package's PDF
reader.

Parser grammar should be based on this extracted representation rather than on
how the visual PDF appears.

## Searching Extracted Statement Evidence

When a failure identifies a specific token, activity description, CUSIP, or
corporate-action annotation, search the extracted statement before writing a
fix.

Example:

```bash
make inspect-statement \
    file="private-data/statements/tdameritrade/TDA - Brokerage Statement_2020-06-30_484.PDF" \
    | grep -C 12 -E '98420U604|R/S|CUSIP'
```

Another example:

```bash
make inspect-statement \
    file="private-data/statements/tdameritrade/TDA - Brokerage Statement_2020-07-31_484.PDF" \
    | grep -C 6 -E 'TO OPEN|TO CLOSE|Commission/Fee'
```

Inspect enough surrounding evidence to understand the complete grammar.

Do not patch only the first failing token when nearby rows may reveal a larger
capability.

## Archive Smoke Testing

Use the real private archive after unit tests are green.

Smoke-test the first statement:

```bash
make smoke-archive \
    folder="private-data/statements/tdameritrade" \
    limit=1
```

Test progressively farther into the archive:

```bash
make smoke-archive \
    folder="private-data/statements/tdameritrade" \
    limit=8
```

The smoke runner processes statements in deterministic filename order and
stops on the first unsupported statement unless configured otherwise.

Typical output:

```text
[01/08] PASS TDA - Brokerage Statement_2020-03-31_484.PDF
         broker=tdameritrade processor=tdameritrade.monthly_2020
         period=2020-03-01..2020-03-31 account=...
         positions=5 events=53 (...)

...

[08/08] PASS TDA - Brokerage Statement_2020-10-31_484.PDF
         broker=tdameritrade processor=tdameritrade.monthly_2020
         period=2020-10-01..2020-10-31 account=...
         positions=0 events=13 (...)
```

A smoke-test `PASS` means the real statement traveled through the public parsing
pipeline without an exception.

Smoke testing complements unit tests; it does not replace them.

## Development Workflow for a New Failure

When the archive stops on a new statement, follow this sequence.

### 1. Stop at the first failure

Do not immediately modify multiple parsers or run far ahead through the archive.

Record the exact exception and source row.

Example:

```text
UnknownActivityError:
Unable to parse TD Ameritrade security transfer row:
...
UVXY Sep 18 20 30.0 C EXPIRATION
```

### 2. Inspect the real statement

Use `make inspect-statement` and search for the failing grammar plus surrounding
rows.

Determine whether the problem is:

* a new identifier
* a new grammar variant
* a new economic capability
* or an actual statement-format revision

### 3. Choose the smallest correct extension point

Examples discovered during real archive development:

```text
CUSIP instead of ticker
    → reference/identifiers.py

XSPA reverse split
    → activity/corporate_actions.py

SNAP/VOD option trades
    → activity/options.py

UVXY option expiration
    → activity/option_expirations.py
```

### 4. Add representative regression tests

Tests should reproduce the real extracted row shape.

Do not simplify a fixture merely to make the current regular expression pass.

The real statement is the evidence. Production grammar should adapt to the
proven statement shape.

### 5. Run all quality gates

At minimum:

```bash
make format
make lint
make typecheck
make coverage
```

Coverage must remain:

```text
100%
```

### 6. Re-run the archive from the beginning

Never test only the newly failing month.

For example:

```bash
make smoke-archive \
    folder="private-data/statements/tdameritrade" \
    limit=8
```

Previously proven statements must continue to pass.

This is how historical behavior remains locked.

### 7. Commit meaningful capability checkpoints

When a coherent extension is complete and the historical archive remains
green, commit it before moving to the next unsupported case.

Examples:

```text
Add TD Ameritrade corporate action support
Add TD Ameritrade option trade support
Add TD Ameritrade option expiration support
```

Avoid mixing unrelated future grammar into the same checkpoint.

## Refactoring Rule

Refactoring and new statement behavior should normally be separate operations.

When a subsystem becomes difficult to maintain:

1. refactor existing proven behavior first;
2. retain 100% coverage;
3. rerun the real archive;
4. verify the same statements pass and the same unsupported statement still
   fails;
5. commit the behavior-neutral refactor;
6. only then add the new capability.

This rule was used when the original TD Ameritrade `activity.py` grew too large.

It was split into:

```text
activity/
├── __init__.py
├── rows.py
├── trades.py
├── cash.py
├── income.py
├── transfers.py
└── corporate_actions.py
```

The corresponding tests were then split to mirror the production structure.

The proof of a successful refactor was:

```text
previously proven statements → still PASS
next unsupported statement   → still FAIL for the same reason
coverage                     → still 100%
```

That is the standard for behavior-neutral refactoring.

## Test Structure

Tests should mirror production structure where practical.

For example:

```text
src/brokerage_statements/processors/tdameritrade/activity/
├── __init__.py
├── rows.py
├── trades.py
├── options.py
├── option_expirations.py
├── cash.py
├── income.py
├── transfers.py
└── corporate_actions.py
```

maps to:

```text
tests/processors/tdameritrade/activity/
├── test_init.py
├── test_rows.py
├── test_trades.py
├── test_options.py
├── test_option_expirations.py
├── test_cash.py
├── test_income.py
├── test_transfers.py
└── test_corporate_actions.py
```

`test_init.py` tests orchestration and precedence.

Focused module tests own the detailed grammar for their corresponding
production module.

This makes it immediately clear which production file a test suite protects.

## What Not to Do

Do not:

* silently ignore unknown activity
* treat unknown CUSIPs as ticker symbols
* guess security identity without evidence
* add broad fallback regular expressions
* mutate a proven processor for a materially different statement revision
* put every activity grammar into one large parser
* put transaction-specific parsing logic into `monthly_2020.py`
* weaken real-statement regression tests to satisfy production code
* mix behavior-changing work into a refactor without necessity
* declare a statement supported merely because processor detection succeeds

Fail loudly and extend deliberately.

## Definition of Proven Support

A historical statement is considered proven when:

```text
PDF extraction succeeds
broker detection is deterministic
processor selection is deterministic
statement identity parses correctly
positions parse correctly
activity parses without unknown rows
pending trades parse correctly
normalized domain objects validate
unit and branch coverage remain 100%
all previously proven archive statements still pass
```

As reconciliation capabilities are added, reconciliation will become an
additional requirement for a fully proven statement.

## Installation

```bash
pip install brokerage-statements
```

Or with `uv`:

```bash
uv add brokerage-statements
```
