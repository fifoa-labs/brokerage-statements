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
unresolved security identities, malformed recognized rows, and invalid
processor output fail explicitly rather than being silently ignored or guessed.

Version `0.2.0` includes real-world statement parsing for both TD Ameritrade and
Charles Schwab, validated against the complete current private historical
corpus for both brokerages.

The package intentionally focuses on statement processing and normalization.
It is not a portfolio manager, brokerage API, trading system, tax engine, lot
reconstruction engine, or Beancount-specific importer.

* **PyPI:** https://pypi.org/project/brokerage-statements/
* **Source:** https://github.com/fifoa-labs/brokerage-statements
* **License:** MIT

## Current Status

The package currently includes:

* Page-aware PDF text extraction
* SHA-256 statement source identity
* Deterministic brokerage detection
* Broker-scoped processor selection
* Strict processor ambiguity detection
* Broker-neutral security, position, and event domain models
* Traceable source evidence attached to normalized results
* Exact `Decimal` handling for financial quantities and amounts
* Focused processor packages for TD Ameritrade and Charles Schwab
* Logical activity-row reconstruction before economic normalization
* External cash-transfer parsing
* Security-transfer parsing
* Interest-income parsing
* Equity trade parsing for supported TD Ameritrade statements
* Option trade parsing for supported TD Ameritrade statements
* Option expiration parsing
* Regulatory and brokerage fee parsing
* Margin-interest expense parsing
* Pending-trade parsing
* Reverse-split normalization
* Cash-in-lieu normalization
* Broker-neutral position-adjustment normalization
* CUSIP-to-symbol reference resolution for observed statement identifiers
* Dedicated handling for final TD Ameritrade-to-Schwab transition statements
* Private archive inspection and smoke-test tooling
* Fully typed public package
* 100% branch test coverage

## Proven Historical Support

The current private corpus contains:

```text
TD Ameritrade
    46 statements
    2020-03 → 2023-12

Charles Schwab
    32 statements
    2023-11 → 2026-06

Total
    78 statements
```

All current private statements parse successfully through the public parsing
pipeline.

A statement is not considered supported merely because a processor recognizes
it. Real support is earned by successfully processing the historical statement
through extraction, broker detection, processor selection, section discovery,
normalization, domain validation, and archive smoke testing.

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

Observed TD Ameritrade support includes:

* Statement identity and reporting period
* Positions
* Settled equity trades
* Pending trades
* Option trades
* Option expirations
* Regulatory fees
* Option commissions and fees
* External cash deposits and withdrawals
* Known internal cash movements
* Security transfers
* TD-to-Schwab migration transfers
* Interest income
* Insured-deposit interest
* Margin-interest expense
* Reverse-split activity
* Cash in lieu
* Mandatory reorganization fees
* Observed CUSIP resolution
* Final transition statements

The claim is not that every TD Ameritrade statement ever produced is supported.
The claim is that the complete current private TD Ameritrade archive is proven.

## Proven Charles Schwab Support

The complete current private Charles Schwab historical corpus contains 32
monthly statements spanning:

```text
November 2023 → June 2026
```

All 32 statements parse successfully through:

```text
charlesschwab.monthly_2023
```

The processor has remained stable across the complete observed range. New
historical behavior was added through focused capability modules rather than by
creating increasingly broad conditionals inside the processor.

Observed Charles Schwab support includes:

* Schwab One statement detection
* Statement account identity
* Statement period parsing
* Account-summary discovery
* Position-summary discovery
* Optional asset-class sections
* Equity positions
* Other-asset and warrant positions
* Optional transaction-detail sections
* Multi-page transaction-detail ranges
* Logical transaction-row reconstruction
* Inherited transaction dates
* Physically split `Other Activity` categories
* Wrapped transaction descriptions
* TD-to-Schwab cash migration deposits
* TD-to-Schwab incoming security transfers
* Schwab One interest income
* Reverse splits represented by paired mechanical rows
* Removal-only reverse-split activity
* Cash-in-lieu redemptions
* Position adjustments that explicitly remove a holding
* Zero-activity monthly statements

Examples of real historical capability boundaries discovered during Schwab
development include:

```text
2023-11
    incoming cash migration
    incoming security migration
    Schwab One interest

2024-02
    paired UAVS reverse split

2024-10
    terminal reverse-split removal
    cash in lieu

2025-01
    PHMB position adjustment to zero
```

Each new behavior was implemented at the narrowest correct extension point.

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
logical position and activity parsing
    ↓
focused economic normalization
    ↓
broker-neutral positions and events
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

Current structure:

```text
processors/
├── tdameritrade/
│   ├── __init__.py
│   ├── monthly_2020.py
│   ├── transition_2023.py
│   ├── identity.py
│   ├── sections.py
│   ├── positions.py
│   ├── pending.py
│   └── activity/
│       ├── __init__.py
│       ├── _utils.py
│       ├── rows.py
│       ├── trades.py
│       ├── options.py
│       ├── option_expirations.py
│       ├── cash.py
│       ├── income.py
│       ├── expenses.py
│       ├── transfers.py
│       ├── transition_transfers.py
│       └── corporate_actions.py
│
└── charlesschwab/
    ├── __init__.py
    ├── monthly_2023.py
    ├── identity.py
    ├── sections.py
    ├── positions.py
    └── activity/
        ├── __init__.py
        ├── _utils.py
        ├── rows.py
        ├── cash.py
        ├── income.py
        ├── transfers.py
        └── corporate_actions.py
```

Processors orchestrate known statement grammars. They should not become giant
collections of transaction-specific regular expressions.

## Processor Ownership

### `tdameritrade.monthly_2020`

Primary TD Ameritrade monthly grammar.

Proven against:

```text
2020-03 → 2023-10
```

### `tdameritrade.transition_2023`

Final TD Ameritrade-to-Charles-Schwab transition grammar.

Proven against:

```text
2023-11 → 2023-12
```

These statements legitimately omit the normal account-position structure after
assets were transferred to Schwab.

### `charlesschwab.monthly_2023`

Observed Charles Schwab monthly grammar.

Proven against:

```text
2023-11 → 2026-06
```

The observed statement presentation evolves over this period, but the
normalized structure handled by the processor remains compatible.

Later Schwab statements may omit `Transaction Details` entirely when there is
no activity, and individual asset-class sections may legitimately disappear
when the account no longer holds that class.

Those are supported grammar characteristics, not reasons to silently weaken
unrelated validation.

## Activity Architecture

Account activity is intentionally decomposed by responsibility.

TD Ameritrade:

```text
activity/
├── __init__.py
├── _utils.py
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

Charles Schwab:

```text
activity/
├── __init__.py
├── _utils.py
├── rows.py
├── cash.py
├── income.py
├── transfers.py
└── corporate_actions.py
```

The important boundary is:

```text
physical PDF extraction
    ↓
rows.py
    ↓
logical activity rows
    ↓
focused economic parsers
    ↓
normalized domain events
```

`rows.py` owns physical extraction oddities such as wrapped text, inherited
dates, and split category labels.

Focused modules own economic meaning.

`activity/__init__.py` owns orchestration, precedence, grouped-event handling,
and strict unknown-row failure.

This prevents account activity from becoming a single large, fragile parser.

## Broker-Neutral Domain Events

Normalized output includes event models such as:

```text
TradeEvent
CashTransferEvent
IncomeEvent
FeeEvent
SecurityTransferEvent
CorporateActionEvent
OptionExpirationEvent
```

Corporate-action categories currently include:

```text
split
reverse_split
symbol_change
conversion
merger
acquisition
spinoff
cash_in_lieu
reorganization
bankruptcy
worthless_security
position_adjustment
```

A broker-specific description should not be forced into a stronger economic
claim than the source proves.

For example, a Schwab `AdjustPosition` removing PHMB is represented as:

```text
POSITION_ADJUSTMENT
```

rather than being guessed to mean bankruptcy or worthless security.

## Source Evidence

Normalized facts retain source evidence.

Evidence includes fields such as:

* Statement source identity
* Page number
* Section
* Raw logical row text
* Processor name
* Sequence number

When multiple physical rows represent one economic action, one normalized event
may retain multiple evidence occurrences.

This is especially important for corporate actions such as paired reverse-split
rows.

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

reverse split
    → activity/corporate_actions.py

cash in lieu
    → activity/corporate_actions.py

position adjustment
    → activity/corporate_actions.py
```

Do not create a new statement processor merely because a new transaction type
appears.

### Same capability, new observed grammar variant

If an existing capability encounters another legitimate representation of the
same economic event, extend only that capability.

Examples observed during development include:

```text
compact vs spaced PDF extraction
wrapped descriptions
split numeric tokens
different physical row continuations
```

The correct extension point is the focused capability that owns the economic
grammar.

### New observed security identifier

If the grammar is already understood but the statement exposes a new CUSIP or
other security identifier, extend the reference layer:

```text
reference/identifiers.py
```

Do not add identifier-specific exceptions to generic transaction parsers.

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

The first processor was not weakened merely because transition statements
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

Examples:

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

grouped corporate action
    before
generic Other Activity handling
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

* Unknown brokerage institutions
* Unknown statement formats
* Ambiguous broker detection
* Ambiguous processor selection
* Unresolved security identifiers
* Unknown account activity
* Malformed recognized transaction rows
* Unknown corporate-action security descriptions
* Invalid processor output

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
    file="private-data/statements/charlesschwab/Brokerage Statement_2024-10-31_484.PDF"
```

Inspect one page:

```bash
make inspect-statement \
    file="private-data/statements/charlesschwab/Brokerage Statement_2024-10-31_484.PDF" \
    page=4
```

Limit displayed text when useful:

```bash
make inspect-statement \
    file="private-data/statements/charlesschwab/Brokerage Statement_2024-10-31_484.PDF" \
    head=2000
```

The inspection command shows the actual text produced by the package PDF
reader.

Parser grammar should be based on this extracted representation rather than on
how the visual PDF appears.

## Searching Extracted Statement Evidence

When a failure identifies a specific token, activity description, identifier,
or corporate-action annotation, search the extracted statement before writing a
fix.

Example:

```bash
make inspect-statement \
    file="private-data/statements/charlesschwab/Brokerage Statement_2024-10-31_484.PDF" \
    | grep -C 25 -E 'Transaction Details|ReverseSplit|Cash-In-Lieu|UAVS'
```

Another example:

```bash
make inspect-statement \
    file="private-data/statements/charlesschwab/Brokerage Statement_2025-01-31_484.PDF" \
    | grep -C 30 -E 'Transaction Details|AdjustPosition|PHMB'
```

Inspect enough surrounding evidence to understand the complete grammar.

Do not patch only the first failing token when nearby rows may reveal a larger
capability.

## Archive Smoke Testing

Use the real private archive after unit tests are green.

Smoke-test the first TD Ameritrade statement:

```bash
make smoke-archive \
    folder="private-data/statements/tdameritrade" \
    limit=1
```

Smoke-test the first Charles Schwab statement:

```bash
make smoke-archive \
    folder="private-data/statements/charlesschwab" \
    limit=1
```

Test progressively farther:

```bash
make smoke-archive \
    folder="private-data/statements/charlesschwab" \
    limit=20
```

Run complete archives:

```bash
make smoke-archive \
    folder="private-data/statements/tdameritrade"
```

```bash
make smoke-archive \
    folder="private-data/statements/charlesschwab"
```

Expected current results:

```text
TD Ameritrade
    46 / 46 PASS

Charles Schwab
    32 / 32 PASS
```

with processor ownership:

```text
TD Ameritrade
    2020-03 → 2023-10
        tdameritrade.monthly_2020

    2023-11 → 2023-12
        tdameritrade.transition_2023

Charles Schwab
    2023-11 → 2026-06
        charlesschwab.monthly_2023
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

Examples discovered during real archive development:

```text
new CUSIP
    → reference/identifiers.py

TD XSPA reverse split
    → tdameritrade/activity/corporate_actions.py

TD SNAP/VOD option trades
    → tdameritrade/activity/options.py

TD UVXY option expiration
    → tdameritrade/activity/option_expirations.py

TD margin interest
    → tdameritrade/activity/expenses.py

TD-to-Schwab security delivery
    → tdameritrade/activity/transition_transfers.py

TD final transition statement structure
    → tdameritrade/transition_2023.py

Schwab wrapped/inherited physical activity rows
    → charlesschwab/activity/rows.py

Schwab migration cash
    → charlesschwab/activity/cash.py

Schwab migration securities
    → charlesschwab/activity/transfers.py

Schwab reverse split
    → charlesschwab/activity/corporate_actions.py

Schwab cash in lieu
    → charlesschwab/activity/corporate_actions.py

Schwab position adjustment
    → charlesschwab/activity/corporate_actions.py
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

For release-level validation:

```bash
make release-check
```

### 6. Re-run the archive from the beginning

Never test only the newly failing month.

For example:

```bash
make smoke-archive \
    folder="private-data/statements/charlesschwab"
```

Previously proven statements must continue to pass.

This is how historical behavior remains locked.

### 7. Commit meaningful capability checkpoints

When a coherent extension is complete and the historical archive remains green,
commit it before moving to the next unsupported case.

Avoid mixing unrelated future grammar into the same checkpoint.

## Refactoring Rule

Refactoring and new statement behavior should normally be separate operations.

When a subsystem becomes difficult to maintain:

1. refactor existing proven behavior first;
2. retain 100% branch coverage;
3. rerun the real archive;
4. verify previously passing statements still pass;
5. verify the next known unsupported statement still fails for the same reason,
   when applicable;
6. commit the refactor;
7. only then add new statement behavior.

This rule was used during both TD Ameritrade and Charles Schwab development.

The point of a refactor is to change structure without quietly changing the
already-proven grammar.

## Test Structure

Tests mirror production structure where practical.

Examples:

```text
src/brokerage_statements/processors/charlesschwab/activity/rows.py
    ↔
tests/processors/charlesschwab/activity/test_rows.py
```

```text
src/brokerage_statements/processors/charlesschwab/activity/corporate_actions.py
    ↔
tests/processors/charlesschwab/activity/test_corporate_actions.py
```

```text
src/brokerage_statements/processors/tdameritrade/positions.py
    ↔
tests/processors/tdameritrade/test_positions.py
```

Package `test_init.py` modules are used when a package `__init__.py` owns
meaningful orchestration or export behavior.

Tests should protect behavior, not merely exercise lines.

## Quality Gate

The project expects:

```bash
make format
make lint
make typecheck
make coverage
```

Release-level validation uses:

```bash
make release-check
```

The test suite requires:

```text
100% branch coverage
```

Lint, type checking, tests, coverage, build validation, and distribution checks
must remain green before a release is considered ready.

## Public Responsibility

`brokerage-statements` answers:

```text
What did the brokerage statement say?
```

It intentionally does not yet answer:

```text
What complete historical ledger reconstructs these statements?
```

The package normalizes statement facts.

Future reconstruction may include:

* Cross-statement duplicate suppression
* Pending-to-settled matching
* Security identity continuity
* Lot inventory
* FIFO/LIFO/specific-lot selection
* Cost-basis reconstruction
* Corporate-action basis transformation
* External transfer pairing
* Migration-boundary reconciliation
* Cash reconciliation
* Position reconciliation
* Beancount rendering

Those responsibilities should not be forced into broker-specific PDF processors.

## Definition of Proven Support

A processor is considered proven for a statement only when all of the following
succeed:

```text
PDF extraction
broker detection
processor selection
required structural discovery
logical row reconstruction
economic normalization
domain validation
unit/regression tests
real archive smoke testing
```

A successful parse must not depend on silently discarded unknown rows.

Historical support is therefore an evidence-backed property of a processor, not
just a claim in documentation.

## Current Milestone

`brokerage-statements` `0.2.0` currently has complete private-archive parsing
coverage for both supported brokerage families:

```text
TD Ameritrade
    46 / 46 PASS
    2020-03 → 2023-12

Charles Schwab
    32 / 32 PASS
    2023-11 → 2026-06

Combined
    78 / 78 PASS
```

The current processor library demonstrates the intended extension model:

```text
proven processor
    stays stable

new economic behavior
    focused capability

new legitimate grammar representation
    focused capability extension

materially different document structure
    new processor
```

That architecture is the foundation for expanding brokerage support without
turning statement parsing into a single fragile parser.
