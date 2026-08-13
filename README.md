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

TD Ameritrade statement parsing is implemented and validated against a private
historical corpus spanning March 2020 through December 2023.

Charles Schwab statement support is the next major brokerage implementation and
will use the same broker-detection, isolated-processor, and capability-extension
architecture.

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
* TD Ameritrade transition-to-Schwab security-transfer parsing
* TD Ameritrade reverse-split activity handling
* TD Ameritrade cash-in-lieu parsing
* TD Ameritrade mandatory reorganization fee parsing
* TD Ameritrade interest-income parsing
* TD Ameritrade insured-deposit interest parsing
* TD Ameritrade margin-interest expense parsing
* TD Ameritrade pending-trade parsing
* CUSIP-to-symbol reference resolution for observed statement identifiers
* Dedicated handling for final TD Ameritrade-to-Schwab transition statements
* Private archive inspection and smoke-test tooling
* Fully typed public package
* 100% branch test coverage

## Proven TD Ameritrade Support

The complete private TD Ameritrade historical corpus currently contains 46
monthly statements spanning:

```text
March 2020 → December 2023
```

All 46 statements parse successfully through the public parsing pipeline.

The processor boundary is:

```text
2020-03 → 2023-10
    tdameritrade.monthly_2020

2023-11 → 2023-12
    tdameritrade.transition_2023
```

The normal monthly processor remained stable through 44 consecutive historical
statements.

The final November and December 2023 statements materially changed structure as
the account transitioned to Charles Schwab. Rather than weakening the proven
monthly processor by making required sections globally optional, those
statements are handled by a dedicated transition processor.

This is the intended processor architecture of the project.

A statement is not considered supported merely because a processor recognizes
it. Real support is earned by successfully processing the historical statement
through extraction, broker detection, processor selection, section discovery,
normalization, and validation.

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
SHA-256 source identity
    ↓
broker detection
    ↓
broker-scoped processor selection
    ↓
statement identity and section discovery
    ↓
focused section and activity parsers
    ↓
normalized positions and events
    ↓
strict validation
    ↓
ParsedStatement
```

Broker detection and statement-format detection are intentionally separate.

Broker detection answers:

```text
Which brokerage institution produced this statement?
```

Processor selection then answers:

```text
Which known statement grammar from that broker produced it?
```

Once a brokerage institution is identified, only processors belonging to that
broker are allowed to compete for the statement.

## Processor Architecture

A statement processor represents a known statement layout or revision.

TD Ameritrade currently has two proven processors:

```text
processors/
└── tdameritrade/
    ├── monthly_2020.py
    ├── transition_2023.py
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
        ├── expenses.py
        ├── transfers.py
        ├── transition_transfers.py
        └── corporate_actions.py
```

### `tdameritrade.monthly_2020`

The primary TD Ameritrade monthly grammar.

It is proven against 44 consecutive real statements from March 2020 through
October 2023.

### `tdameritrade.transition_2023`

The final TD Ameritrade-to-Charles-Schwab transition grammar.

It handles the November and December 2023 statements, which intentionally omit
the normal `Account Positions` section after assets were transferred to Schwab.

Transition statements are identified using strong transition evidence rather
than merely by the absence of positions.

`monthly_2020.py` remains intentionally small. It owns its statement revision
and orchestrates focused parsing capabilities.

It should not become a large collection of transaction-specific regular
expressions.

## Activity Architecture

TD Ameritrade account activity is intentionally decomposed by economic
capability:

```text
activity/
├── __init__.py
├── rows.py
├── trades.py
├── options.py
├── option_expirations.py
├── cash.py
├── income.py
├── expenses.py
├── transfers.py
├── transition_transfers.py
└── corporate_actions.py
```

The modules have focused responsibilities:

* `rows.py` reconstructs logical activity rows from page-aware statement text.
* `trades.py` parses settled equity trades.
* `options.py` parses option trades.
* `option_expirations.py` parses option expirations.
* `cash.py` parses external cash movement and recognizes known internal cash
  journals.
* `income.py` parses supported income activity.
* `expenses.py` parses supported expense activity such as margin interest.
* `transfers.py` parses ordinary security transfers.
* `transition_transfers.py` parses TD-to-Schwab transition deliveries.
* `corporate_actions.py` handles supported reorganization activity.

`activity/__init__.py` owns orchestration and parser precedence rather than
individual financial grammars.

This prevents account activity from becoming a single large, fragile parser.

## Extension Rule

This is the most important maintenance rule in the project.

When a new real statement fails, first determine **what changed**.

### Same statement format, new economic capability

If the statement structure is still the same but exposes a new kind of
activity, add a focused capability.

Examples:

```text
option trade
    → activity/options.py

option expiration
    → activity/option_expirations.py

margin interest
    → activity/expenses.py

reverse split or reorganization
    → activity/corporate_actions.py
```

Do not create a new statement processor merely because a new transaction type
appears.

### Same capability, new observed grammar variant

If an existing capability encounters another legitimate representation of the
same economic event, extend only that capability.

For example, TD Ameritrade represented option expiration using both:

```text
Delivered - Other ... EXPIRATION
```

and:

```text
Received - Other ... EXPIRATION
```

Both are option expiration.

The correct extension point is therefore:

```text
activity/option_expirations.py
```

not the statement processor.

### New observed security identifier

If the grammar is already understood but the statement exposes a new CUSIP or
other security identifier, extend the reference layer:

```text
reference/identifiers.py
```

Do not add identifier-specific exceptions to transaction parsers.

### Materially different statement format or revision

If a later statement changes document structure materially, such as:

* different required sections
* incompatible section layout
* materially different identifying markers
* different terminal or migration semantics
* behavior that cannot be safely supported without weakening a proven
  processor

then add a new processor.

The TD Ameritrade archive demonstrates this directly:

```text
tdameritrade.monthly_2020
    2020-03 → 2023-10

tdameritrade.transition_2023
    2023-11 → 2023-12
```

The first processor was not weakened merely because the transition statements
legitimately contained no account-position section.

## Do Not Keep Bending a Proven Processor

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

Is this broker-specific transition activity?
    → focused transition capability

Is the actual statement format materially different?
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

TD-to-Schwab transition transfer
    before
generic security transfer
```

A row can resemble a generic transaction structurally while representing a more
specific economic event.

The specific parser therefore receives the row first.

The dispatcher in `activity/__init__.py` owns this precedence.

Individual capability modules should not need to know about unrelated
capabilities.

## Strict Failure

The package intentionally fails on unknown or ambiguous behavior.

It does not silently skip unrecognized activity.

Examples include:

* unknown statement formats
* ambiguous broker detection
* ambiguous processor selection
* unresolved security identifiers
* unknown account activity
* malformed recognized transaction rows
* invalid processor output

A successful parse therefore means more than "some values were extracted."

The parser has accounted for the statement according to a known grammar.

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
    file="private-data/statements/tdameritrade/TDA - Brokerage Statement_2023-11-30_484.PDF"
```

Inspect one page:

```bash
make inspect-statement \
    file="private-data/statements/tdameritrade/TDA - Brokerage Statement_2023-11-30_484.PDF" \
    page=2
```

Limit displayed text when useful:

```bash
make inspect-statement \
    file="private-data/statements/tdameritrade/TDA - Brokerage Statement_2023-11-30_484.PDF" \
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
    file="private-data/statements/tdameritrade/TDA - Brokerage Statement_2023-06-30_484.PDF" \
    | grep -C 15 -E '74347Y839|74347Y771|R/S|REORGANIZATION'
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
    limit=20
```

Run the complete TD Ameritrade archive:

```bash
make smoke-archive \
    folder="private-data/statements/tdameritrade"
```

The expected current result is:

```text
46 / 46 PASS
```

with:

```text
2020-03 → 2023-10
    processor=tdameritrade.monthly_2020

2023-11 → 2023-12
    processor=tdameritrade.transition_2023
```

The smoke runner processes statements in deterministic filename order and
stops on the first unsupported statement unless configured otherwise.

A smoke-test `PASS` means the real statement traveled through the parsing
pipeline without an exception.

Smoke testing complements unit tests; it does not replace them.

## Development Workflow for a New Failure

When the archive stops on a new statement, follow this sequence.

### 1. Stop at the first failure

Do not immediately modify multiple parsers or run far ahead through the archive.

Record the exact exception and source row.

### 2. Inspect the real statement

Use `make inspect-statement` and search for the failing grammar plus surrounding
rows.

Determine whether the problem is:

* a new identifier
* a new grammar variant
* a new economic capability
* or an actual statement-format revision

### 3. Choose the smallest correct extension point

Examples discovered during real TD Ameritrade archive development:

```text
new CUSIP
    → reference/identifiers.py

XSPA reverse split
    → activity/corporate_actions.py

SNAP/VOD option trades
    → activity/options.py

UVXY option expiration
    → activity/option_expirations.py

margin interest charge
    → activity/expenses.py

TD-to-Schwab security delivery
    → activity/transition_transfers.py

final transition statement structure
    → transition_2023.py
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
    folder="private-data/statements/tdameritrade"
```

Previously proven statements must continue to pass.

This is how historical behavior remains locked.

### 7. Commit meaningful capability checkpoints

When a coherent extension is complete and the historical archive remains
green, commit it before moving to the next unsupported case.

Avoid mixing unrelated future grammar into the same checkpoint.

## Refactoring Rule

Refactoring and new statement behavior should normally be separate operations.

When a subsystem becomes difficult to maintain:

1. refactor existing proven behavior first;
2. retain 100% branch coverage;
3. rerun the real archive;
4. verify the same statements pass and
