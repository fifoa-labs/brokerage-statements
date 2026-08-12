# brokerage-statements — Project Blueprint

**Repository:** `fifoa-labs/brokerage-statements`  
**Distribution:** `brokerage-statements`  
**Import package:** `brokerage_statements`  
**Status:** Active design and implementation  
**Blueprint version:** 1.0  
**Last updated:** 2026-08-11

---

## 1. Purpose of This Blueprint

This document is the implementation blueprint and architectural source of truth
for `brokerage-statements`.

It combines two kinds of content:

- **confirmed requirements** carried forward from the architecture handoff,
  current package behavior, and shared coding standards; and
- **concrete project decisions** made here where those sources intentionally
  left implementation details open.

Those project decisions become authoritative only when this blueprint is
adopted in the repository. Until then, they should be reviewed as the proposed
contract for the next implementation phase.

It converts the original architecture handoff into a concrete plan that can be
followed module by module, release by release, and statement by statement.

Use this blueprint to answer:

- What are we building?
- What are we deliberately not building?
- Which layer owns a behavior?
- When should a new statement require a rule versus a processor?
- What must a processor prove before it is considered stable?
- What does the public API promise?
- How do we preserve historical correctness and source evidence?
- How do we add support for an unknown future statement without destabilizing
  formats that already work?

This blueprint should prevent both of these failure modes:

1. Building abstractions before a real statement proves they are needed.
2. Solving each new statement directly inside a growing broker-specific parser.

The target is a compact, strict, processor-oriented library that remains easy
for one developer to understand.

---

## 2. Authority and Related Documents

The project uses the following authority order:

1. `BLUEPRINT.md` defines package architecture, responsibilities, contracts,
   workflow, and implementation sequence.
2. `CodingStandards.md` defines Python style, documentation, formatting,
   linting, type-checking, testing, and engineering culture.
3. Tests define executable behavior.
4. Processor fixtures define the supported statement grammars.
5. `README.md` describes the supported public behavior for users.
6. Release notes describe behavior introduced by a particular version.

The original architecture handoff remains valuable background, but this
blueprint supersedes it wherever the project has already made a more specific
or updated decision.

`AppStructure.md` does not apply to this package. It governs Django, HTMX, and
DRF application surfaces. `brokerage-statements` is deliberately independent
of Django, HTTP routing, templates, and database models.

If implementation intentionally departs from this blueprint, update the
blueprint in the same change. Do not allow the architecture document and the
codebase to drift silently.

---

## 3. Executive Summary

`brokerage-statements` is a standalone Python library that converts supported
brokerage statements into complete, deterministic, broker-neutral, auditable
Python objects.

The central abstraction is a **statement processor**.

A processor owns one known statement grammar, layout, or revision. It detects
whether it owns a statement, parses every required financial section, emits
normalized domain objects, preserves evidence, and fails explicitly when the
source cannot be interpreted safely.

The core flow is:

```text
PDF path
  ↓
Source validation and SHA-256 identity
  ↓
Deterministic PDF text extraction
  ↓
Broker detection
  ↓
Processor registry
  ↓
Processor matching
  ↓
Exactly one processor selected
  ↓
Strict section and activity parsing
  ↓
Normalized ParsedStatement
  ↓
Statement reconciliation
  ↓
Optional archive continuity checks
```

The architecture is built for this future support request:

> A user uploads one brokerage statement the library has never seen before.

Supporting that statement should normally require one isolated change:

- a reusable activity rule;
- a historical reference fact;
- a reconciliation classification; or
- a new processor revision.

It should not require rewriting an already-proven processor.

---

## 4. Product Mission

Given a supported brokerage PDF, return a complete, normalized, auditable
`ParsedStatement` or raise a useful package exception explaining why the
statement cannot be trusted.

A successful parse means more than finding some transactions. It means the
processor has established, to the level required by its format contract:

- source identity;
- broker identity;
- processor identity;
- account identity;
- statement period;
- recognized financial activity;
- closing positions or explicit proof of zero positions;
- required summary or balance facts;
- source evidence for every normalized result; and
- all required structural and reconciliation checks available at that stage.

A partial parse must never be reported as a successful parse.

---

## 5. Primary Design Objective

The primary design objective is not clever abstraction.

It is:

> A processor can be trusted once proven, and future statement variants can be
> added without destabilizing it.

Every proposed abstraction must pass this test:

> Does this make the next unknown statement easier to support without making
> already-supported statements harder to understand?

If the answer is no, do not add it.

---

## 6. Non-Negotiable Principles

### 6.1 Deterministic behavior

The same input bytes, package version, processor registry, and reference data
must produce the same result or the same exception.

No behavior may depend on:

- filesystem discovery order;
- dictionary insertion accidents;
- locale;
- current time;
- network responses;
- random values;
- mutable global registration order; or
- whichever parser happens to be tried first.

### 6.2 Strict failure semantics

Never silently:

- skip financial activity;
- ignore an unknown candidate row;
- guess a security mapping;
- invent a corporate action;
- fabricate a balancing transaction;
- infer zero positions merely because a positions section is absent;
- accept multiple equally valid processors;
- accept ambiguous activity rules; or
- mutate normalized events to force reconciliation.

### 6.3 Broker-neutral domain

Domain models must not know about:

- PDF libraries;
- regular expressions;
- Schwab labels;
- TD Ameritrade labels;
- parser row shapes;
- Django;
- databases;
- Beancount syntax; or
- rendering targets.

### 6.4 Exact arithmetic

Financial quantities and amounts use `Decimal`.

Floats are rejected at validation boundaries. Non-finite values are rejected.
No economic quantity is rounded merely to match a delivered whole-share amount.

### 6.5 Evidence preservation

Every normalized event and reported position must be traceable to one or more
source occurrences.

### 6.6 Stable processors

Once a processor has meaningful whole-statement fixtures and is released, its
interpretation contract is considered stable.

A new incompatible layout normally receives a new processor revision.

### 6.7 Small public API

Ordinary users should not need to know about readers, detectors, registries,
rules, or processors.

### 6.8 No speculative modules

Do not create a Python module until its implementation and tests are being
added in the same change.

This rule supports the project's 100% branch-coverage requirement and prevents
empty architecture from accumulating.

---

## 7. Initial Scope

### 7.1 Initial brokers

The initial processor families are:

- TD Ameritrade monthly brokerage statements;
- Charles Schwab / Schwab One brokerage statements.

### 7.2 Initial source type

The initial public input is a local, text-based PDF file.

The first PDF reader does not perform OCR.

Scanned, image-only, encrypted, corrupt, or text-empty PDFs must fail
explicitly with source-reading diagnostics.

### 7.3 Initial account currency

The first TD Ameritrade and Schwab processors support USD-denominated account
statements only.

The normalized statement should record its currency. A processor must not
silently treat an explicitly non-USD statement as USD.

### 7.4 Initial normalized capabilities

The package is expected to normalize, when present in a supported format:

- stock, ETF, warrant, and option trades;
- pending and settled trades;
- external deposits and withdrawals;
- dividends and interest;
- brokerage fees;
- internal broker cash movements such as sweep activity;
- security transfers;
- option openings and closings;
- option expiration;
- splits and reverse splits;
- symbol changes and conversions;
- cash in lieu;
- mergers, acquisitions, and reorganizations;
- worthless-security adjustments;
- inactive statements; and
- explicit zero-position statements.

### 7.5 Historical proving archive

The private historical archive is a proving ground, not the public API.

Its role is to reveal:

- processor revisions;
- reusable activity grammars;
- historical security facts;
- reconciliation semantics; and
- genuinely malformed or ambiguous source data.

The public repository must not contain unsanitized personal statements.

---

## 8. Explicit Non-Goals

Do not initially build:

- Django integration;
- database models;
- REST APIs;
- HTMX or template integration;
- Beancount rendering;
- a tax engine;
- wash-sale calculation;
- an elaborate lot-selection engine;
- portfolio performance analytics;
- live brokerage API access;
- trading or order placement;
- a public command-line interface;
- OCR infrastructure;
- remote PDF downloading;
- a generic document parsing framework;
- configurable plugin discovery;
- dozens of service classes; or
- user profiles and privacy workflows.

These may be separate downstream projects or future features. They must not
shape the first parser architecture prematurely.

---

## 9. Current Project State

### 9.1 Released foundation

Version `0.1.0` established the package and release flow:

- `src/` layout;
- `py.typed`;
- Python 3.11–3.14 metadata and CI matrix;
- Ruff formatting and linting;
- strict mypy checking;
- pytest;
- 100% branch coverage requirement;
- wheel and source distribution validation;
- clean-wheel installation testing;
- GitHub Actions CI;
- PyPI Trusted Publishing;
- MIT license; and
- initial README and package exception base.

### 9.2 Foundation implemented during current development

The current working implementation has introduced and tested the first domain
and text primitives:

- exact decimal conversion;
- package-specific decimal errors;
- statement source identity;
- source evidence;
- symbol/equity and option identities;
- broker identity;
- statement periods;
- positions;
- normalized events;
- parsed statements;
- statement pages; and
- page-aware statement text.

### 9.3 Important review gate before the first real processor

The current foundation is a useful first pass, but the first real statement
processor should not be started until the domain hardening decisions in
Section 17 are reviewed and implemented.

Known archive facts already prove that the domain must account for:

- warrants as well as equities;
- multiple source rows supporting one economic event;
- explicit transfer direction;
- pending versus settled trades;
- option open versus close position effect;
- corporate actions with different source and target securities;
- account identity;
- processor identity on the parsed result; and
- statement currency.

It is cheaper to make those corrections now than after processors and public
examples depend on the current field shapes.

---

## 10. Terminology

### Statement source

The original input file and its immutable source identity, including the raw
file SHA-256.

### Statement text

Page-aware text extracted deterministically from the source PDF.

### Broker detector

A small component that determines the brokerage institution using strong,
broker-specific document signatures.

### Processor

A stable adapter for one known statement grammar, layout, or revision.

### Rule

A reusable parser for a recognizable financial activity grammar within a
processor family.

### Source occurrence

One row or row cluster from the extracted statement text that represents or
supports financial data.

### Normalized event

A broker-neutral representation of an economic activity.

### Reference fact

Historical information such as a CUSIP mapping, symbol transformation, or
corporate-action ratio. It is not parsing grammar.

### Reconciliation

Deterministic comparison of normalized results against statement-reported
balances, summaries, positions, and adjacent statements.

### Processor fixture

A sanitized whole-statement text fixture that proves a processor owns and
correctly interprets a statement grammar.

### Rule fixture

A smaller sanitized text fixture that proves one activity grammar.

---

## 11. Architectural Pipeline

The complete intended flow is:

```text
parse_statement(path)
  │
  ├─ normalize and validate path
  ├─ read raw bytes
  ├─ calculate SHA-256
  ├─ create StatementSource
  ├─ extract StatementText from PDF
  ├─ detect Broker
  ├─ select exactly one StatementProcessor
  ├─ parse required sections
  ├─ parse every candidate financial occurrence
  ├─ normalize events, positions, balances, and summaries
  ├─ validate statement completeness
  ├─ run available statement reconciliation
  └─ return ParsedStatement
```

Archive processing later adds:

```text
parse_archive(paths)
  │
  ├─ parse each unique source deterministically
  ├─ group statements by broker and account
  ├─ order by statement period
  ├─ detect overlaps and gaps
  ├─ correlate pending and settled activity
  ├─ verify cross-statement balances and positions
  └─ return statements or a strict archive report
```

---

## 12. Layering and Dependency Direction

The architecture uses one-way dependencies.

```text
public orchestration
├── processors ──> domain, text, reference, exceptions
├── text ─────────> source identity, exceptions
└── reconcile ────> domain, reference, exceptions

reference ────────> domain
domain ───────────> exceptions
```

The exact dependency rules are:

### 12.1 `exceptions`

May depend only on the standard library.

It must not import domain models because domain modules use package exception
classes and circular imports must be avoided.

### 12.2 `domain`

May depend on:

- the standard library; and
- top-level exception classes that do not import domain.

It must not import:

- text extraction;
- processors;
- reference catalogs;
- reconciliation; or
- public orchestration.

### 12.3 `text`

May depend on:

- the standard library;
- source identity models; and
- source-reading exceptions.

It must not know about broker-specific processors or normalized events.

### 12.4 `reference`

May depend on domain security and corporate-action types.

It must not import processors. Historical facts must remain usable by more
than one processor revision.

### 12.5 `processors`

May depend on:

- domain models;
- statement text models;
- reference catalogs; and
- parsing exceptions.

A processor must not read files, configure logging, or run archive workflows.

### 12.6 `reconcile`

May depend on:

- domain models;
- broker identity;
- reference facts; and
- reconciliation exceptions.

It must not mutate normalized events or import concrete processor
implementations.

### 12.7 Public orchestration

The public parsing module may coordinate all lower layers.

No lower layer may import the public parsing module.

---

## 13. Target Package Structure

The following is the intended shape by the time both broker families and
reconciliation are implemented.

Files must still be created only when their implementation and tests are added.

```text
src/brokerage_statements/
├── __init__.py
├── api.py                         # public parse orchestration
├── exceptions.py
├── py.typed
│
├── domain/
│   ├── __init__.py
│   ├── amounts.py
│   ├── evidence.py
│   ├── events.py
│   ├── securities.py
│   └── statements.py
│
├── text/
│   ├── __init__.py
│   ├── models.py
│   └── pdf.py                     # deterministic PDF text reader
│
├── processors/
│   ├── __init__.py
│   ├── base.py                    # protocol and ProcessorMatch
│   ├── detection.py               # broker detection
│   ├── registry.py                # immutable deterministic registry
│   │
│   ├── tdameritrade/
│   │   ├── __init__.py
│   │   ├── monthly_2020.py        # name confirmed by fixtures
│   │   └── rules.py               # split only when naturally necessary
│   │
│   └── charlesschwab/
│       ├── __init__.py
│       ├── schwab_one_2023.py     # name confirmed by fixtures
│       └── rules.py
│
├── reference/
│   ├── __init__.py
│   ├── securities.py
│   └── corporate_actions.py
│
└── reconcile/
    ├── __init__.py
    ├── models.py
    ├── statements.py
    └── continuity.py
```

Tests remain outside the distributable package:

```text
tests/
├── __init__.py
├── test_api.py
├── test_exceptions.py
│
├── domain/
├── text/
├── processors/
│   ├── test_base.py
│   ├── test_detection.py
│   ├── test_registry.py
│   ├── tdameritrade/
│   └── charlesschwab/
├── reference/
├── reconcile/
├── fixtures/
│   ├── tdameritrade/
│   └── charlesschwab/
└── helpers.py
```

Do not place tests under `src/brokerage_statements/`. Coverage treats the
package tree as production code, and tests must not be shipped in the wheel by
accident.

---

## 14. Public API

### 14.1 Initial public surface

The first useful public API should be:

```python
from brokerage_statements import parse_statement

statement = parse_statement("statement.pdf")
```

The initial signature should remain path-focused:

```python
def parse_statement(
    source: str | Path,
) -> ParsedStatement:
    ...
```

Do not add file objects, bytes, URLs, streams, or storage backends until a real
consumer requires them.

### 14.2 Root exports

The root package should eventually export only a small curated surface:

```python
from .api import parse_statement
from .exceptions import BrokerageStatementsError

__all__ = [
    "BrokerageStatementsError",
    "parse_statement",
]
```

Domain consumers may import typed models from:

```python
from brokerage_statements.domain import ParsedStatement, TradeEvent
```

Processor internals should not be re-exported at the root.

### 14.3 Public API behavior

`parse_statement()` must internally:

1. validate the source;
2. compute source identity;
3. extract page-aware text;
4. detect the broker;
5. select exactly one processor;
6. parse the complete statement;
7. validate processor output;
8. run the reconciliation checks available in that release; and
9. return a frozen `ParsedStatement`.

For source-driven operational failures, the public API should raise a
`BrokerageStatementsError` subclass rather than leaking arbitrary internal
exceptions.

Programming errors such as invalid direct construction of a domain dataclass
may still use `ValueError` where appropriate.

### 14.4 Archive API

Do not publish `parse_archive()` until single-statement parsing and processor
contracts are stable.

When introduced, its behavior must be explicitly designed rather than being a
loop around `parse_statement()` with unclear failure handling.

### 14.5 No public serialization yet

Do not promise JSON, dictionaries, Pydantic models, or schema stability until
the domain is proven against both broker families.

Frozen typed dataclasses are the initial public representation.

---

## 15. Data Model Conventions

### 15.1 Immutability

Public domain models use:

```python
@dataclass(frozen=True, slots=True)
```

Collections use tuples, not mutable lists.

Avoid mutable dictionaries in public models. If a mapping becomes necessary,
use an immutable representation or a dedicated typed dataclass.

### 15.2 Ordering

Within one `ParsedStatement`, events preserve source statement order unless a
model explicitly documents a different order.

Do not sort events by type or symbol.

Evidence sequence values provide a stable ordering key when a statement row
cluster creates more than one normalized event.

### 15.3 No generic metadata bags

Do not add fields such as:

```python
metadata: dict[str, object]
```

If a fact matters, give it a typed name and contract.

### 15.4 Validation boundaries

Domain constructors validate universal invariants.

Broker-specific requirements belong in processors or reconciliation.

Examples:

- `Decimal` must be finite: domain invariant.
- TD portfolio summary must contain all zero categories before accepting no
  positions: processor requirement.
- TD cash in lieu counts under securities sold: reconciliation semantics.

---

## 16. Exact Decimal and Sign Conventions

### 16.1 Accepted decimal inputs

The exact conversion helper accepts:

- `Decimal`;
- `int`; and
- decimal strings.

It rejects:

- `float`;
- `bool`;
- empty strings;
- malformed strings;
- NaN; and
- positive or negative infinity.

### 16.2 Money model

Do not introduce a broad `Money` framework yet.

Initial monetary fields use finite `Decimal` values plus the statement's
explicit currency.

### 16.3 Sign convention

Use explicit direction enums wherever direction is a distinct concept.

Recommended conventions:

- trade quantity: positive magnitude;
- trade side: `BUY` or `SELL`;
- external transfer amount: positive magnitude;
- external transfer direction: `DEPOSIT` or `WITHDRAWAL`;
- fee amount: positive magnitude;
- income amount: positive magnitude;
- security transfer quantity: positive magnitude;
- security transfer direction: `IN` or `OUT`;
- position quantity: signed, because short positions may be negative;
- corporate-action quantities: economic quantities as reported or derived;
- corporate-action cash: positive magnitude with semantics supplied by the
  action type.

Do not encode direction sometimes by enum and sometimes by sign for the same
event family.

### 16.4 Precision

Do not quantize security quantities merely for display.

For example, a 1:3 reverse split of 500 shares has an exact economic quantity
of repeating 166.666..., even if the broker delivers 166 whole shares and pays
cash for the fraction.

Currency quantization belongs at a clearly documented statement or
reconciliation boundary, not inside general decimal conversion.

---

## 17. Domain Hardening Before the First Processor

The current first-pass domain should be hardened before real broker parsing.
These are known requirements, not speculative features.

### 17.1 Centralize the `Security` union

The shared security union must live in `domain/securities.py` and be exported
from there.

Do not redefine the same union in `events.py` and `statements.py`.

### 17.2 Replace overly narrow equity identity

The archive contains warrants and may contain other symbol-identified
instruments. A class named `EquitySecurity` is too narrow if it will also hold
`DWACW`, `DJTWW`, or similar instruments.

Prefer a neutral identity such as:

```python
@dataclass(frozen=True, slots=True)
class SymbolSecurity:
    symbol: str
```

Then:

```python
Security = SymbolSecurity | OptionSecurity
```

Instrument classification may be added separately when a real use case needs
it. Identity and taxonomy should not be conflated prematurely.

### 17.3 Allow multiple evidence occurrences

One economic event may be supported by multiple source rows.

Event evidence should therefore be a non-empty tuple:

```python
evidence: tuple[SourceEvidence, ...]
```

This is required for corporate-action clusters such as:

- delivered old security;
- received replacement security;
- reorganization fee; and
- cash in lieu.

A convenience constructor may accept one item internally, but the normalized
model should not be limited to one occurrence.

### 17.4 Add explicit transfer direction

Replace signed security-transfer quantity with:

```python
direction: SecurityTransferDirection
quantity: Decimal
```

where quantity is positive.

### 17.5 Preserve trade state

Trade normalization needs fields for known source semantics:

```python
status: TradeStatus          # pending or settled
position_effect: PositionEffect | None  # open or close
settlement_date: date | None
```

Do not infer open/close from buy/sell alone.

### 17.6 Model source and target security for corporate actions

A corporate action must support historical transformations:

```python
source_security: Security
target_security: Security | None
```

This is required for cases such as:

```text
DWACW → DJTWW
```

Do not model that transformation as a permanent symbol alias.

### 17.7 Add account and processor identity

`ParsedStatement` should include:

```python
account_id: str
processor_name: str
currency: str
```

The account identifier may be masked if that is all the source provides. It
must be normalized consistently without inventing missing digits.

### 17.8 Preserve position evidence

A reported closing position should carry its source evidence so reconciliation
and diagnostics can identify the exact statement row.

### 17.9 Add internal broker movement only when implementing it

FDIC sweep activity is already known, so an internal cash-movement event will
be needed by the TD processor.

Add it with the first fixture that exercises the behavior, not as an empty
placeholder beforehand.

### 17.10 Domain hardening acceptance gate

Do not begin broker-specific processor implementation until:

- the hardened models are tested;
- all public names are re-exported intentionally;
- strict mypy passes;
- Ruff passes; and
- branch coverage remains 100%.

---

## 18. Source Identity and Evidence

### 18.1 `StatementSource`

`StatementSource` identifies the input bytes, not merely a filename.

Recommended fields:

```python
@dataclass(frozen=True, slots=True)
class StatementSource:
    path: Path
    sha256: str
```

Validation should eventually require:

- a non-empty path;
- a 64-character hexadecimal SHA-256;
- normalized lowercase digest text.

The hash is calculated from raw PDF bytes before text extraction.

### 18.2 `SourceEvidence`

Recommended fields:

```python
@dataclass(frozen=True, slots=True)
class SourceEvidence:
    source: StatementSource
    page: int | None = None
    section: str | None = None
    raw_text: str | None = None
    processor: str | None = None
    reference: str | None = None
    sequence: int | None = None
```

Evidence should preserve:

- source file identity;
- one-based page number;
- section name;
- extracted source text;
- processor name;
- broker reference or correlation key; and
- stable source order.

### 18.3 Evidence is not logging

The library must not automatically print or log raw evidence. Statement text
may contain personal and financial information.

Exceptions may retain structured evidence for caller-controlled diagnostics.

### 18.4 Evidence completeness rule

Every normalized event and reported position must have at least one evidence
item before a processor may return successfully.

Derived reconciliation checks should cite the evidence used to calculate both
sides when practical.

---

## 19. Security Identity

### 19.1 Domain identity

The domain initially distinguishes:

- symbol-identified securities; and
- option contracts.

A symbol-identified security preserves the historical symbol printed for that
period.

An option identity contains:

- underlying symbol;
- expiration date;
- call or put right; and
- exact strike price.

### 19.2 Option placeholders

A broker-printed `-` in a Symbol/CUSIP column is not a security symbol.

When the contract description provides the identity, parse it from the
description.

### 19.3 Historical correctness

Do not alias historically distinct symbols merely to make closing positions
reconcile.

For example:

```text
DWACW → DJTWW
```

must be represented by the appropriate dated corporate action once established
from evidence.

### 19.4 Security reference catalog

CUSIP and CINS resolution belongs in `reference/securities.py`.

The catalog should support date-aware facts rather than an unqualified mapping
when identity changes over time.

A future record may resemble:

```python
@dataclass(frozen=True, slots=True)
class SecurityReference:
    identifier: str
    security: Security
    valid_from: date | None = None
    valid_to: date | None = None
    note: str | None = None
```

Do not implement this record until the first fixture needs catalog resolution.

### 19.5 Unknown and ambiguous identifiers

Unknown identifiers fail with a structured unknown-security exception.

Multiple valid historical resolutions fail with an ambiguous-security
exception.

No processor may guess based only on a company-name resemblance.

---

## 20. Statement-Level Domain

### 20.1 Broker

Broker identity is an enum, initially:

```python
class Broker(StrEnum):
    TD_AMERITRADE = "tdameritrade"
    CHARLES_SCHWAB = "charlesschwab"
```

### 20.2 Statement period

Statement periods are inclusive and must satisfy:

```text
start <= end
```

### 20.3 Account identity

The normalized statement records the account identifier printed by the source.

Do not create missing account digits. Do not use the source filename as account
identity.

### 20.4 Positions

Closing positions should support:

- security identity;
- exact signed quantity;
- source evidence; and
- optional reported price, market value, and cost basis when provided.

Optional valuation fields should be added when the first processor extracts
them and reconciliation needs them.

### 20.5 Statement balances

A broker-neutral statement balance model will be needed for reconciliation.
Expected normalized fields include, when the source provides them:

- opening cash;
- closing cash;
- opening account value; and
- closing account value.

Do not force every broker format to fabricate unavailable fields.

### 20.6 Activity summaries

Broker-reported summary categories should be normalized into a small typed
model before reconciliation.

The raw broker label remains evidence. The domain classification should not be
a free-form broker label.

### 20.7 `ParsedStatement`

The mature statement model is expected to contain:

```python
@dataclass(frozen=True, slots=True)
class ParsedStatement:
    source: StatementSource
    broker: Broker
    processor_name: str
    account_id: str
    currency: str
    period: StatementPeriod
    events: tuple[NormalizedEvent, ...]
    positions: tuple[Position, ...]
    balances: StatementBalances | None = None
    activity_summary: StatementActivitySummary | None = None
```

This is a target contract. Add balance and summary models only alongside real
processor extraction and tests.

---

## 21. Normalized Event Families

### 21.1 Trade event

Represents an executed or pending purchase or sale.

Expected semantics:

- security identity;
- trade date;
- optional settlement date;
- buy or sell side;
- pending or settled status;
- optional open or close position effect;
- positive quantity;
- non-negative price;
- exact statement amount semantics documented by the processor contract;
- one or more evidence occurrences.

Do not encode option open/close semantics in broker-specific description text
only.

### 21.2 External cash transfer

Represents money entering or leaving the brokerage account from an external
source.

Direction is explicit. Amount is positive.

### 21.3 Income event

Represents income such as:

- dividend;
- interest; or
- another explicitly classified income type.

Amount is positive.

### 21.4 Fee event

Represents a brokerage fee as a positive amount with an optional normalized
description or fee type.

A fee associated with a corporate-action cluster remains a separate economic
event while sharing cluster evidence or a correlation reference.

### 21.5 Internal broker movement

Represents cash movement internal to the brokerage account structure, such as
an FDIC sweep.

It must not be mistaken for an external deposit, withdrawal, or income.

### 21.6 Security transfer

Represents securities entering or leaving the account without being bought or
sold.

Direction is explicit and quantity is positive.

### 21.7 Corporate action

Represents economic transformations including:

- split;
- reverse split;
- symbol change;
- conversion;
- merger;
- acquisition;
- spinoff;
- cash in lieu;
- reorganization;
- bankruptcy; and
- worthless security.

The event supports source and target securities where appropriate.

### 21.8 Option expiration

Represents expiration of an option contract with a positive contract quantity.

It is not a security transfer.

### 21.9 Event evidence

Every event carries a non-empty tuple of evidence occurrences.

### 21.10 No artificial balancing events

Reconciliation may explain a difference using statement classification rules,
but it may never invent a normalized event that did not occur economically.

---

## 22. Statement Text Model

### 22.1 `StatementPage`

Represents one extracted PDF page:

```python
@dataclass(frozen=True, slots=True)
class StatementPage:
    number: int
    text: str
```

Page numbers are one-based.

### 22.2 `StatementText`

Represents ordered page-aware extraction:

```python
@dataclass(frozen=True, slots=True)
class StatementText:
    pages: tuple[StatementPage, ...]
```

The combined `text` property is useful for document-level matching.

Processor parsing should remain page-aware so evidence never has to reverse-map
a match from one giant string back to a page.

### 22.3 Empty text

The value model may permit an empty tuple for isolated tests.

The production PDF reader must reject a source that yields no pages or no
meaningful text.

### 22.4 Text normalization policy

The reader may normalize only deterministic extraction artifacts such as:

- line endings;
- non-breaking spaces when proven necessary; and
- trailing whitespace when it does not destroy row structure.

Do not aggressively rewrite spaces, punctuation, minus signs, or wrapping
before processors have had a chance to interpret the source.

Evidence `raw_text` means raw text from the package's deterministic extraction
layer, not raw PDF binary content.

---

## 23. PDF Text Reader

### 23.1 Reader responsibility

The PDF reader is responsible only for:

- opening the local PDF;
- producing ordered page text;
- preserving page numbers;
- raising useful source-reading errors; and
- remaining deterministic.

It does not detect brokers or parse financial activity.

### 23.2 Reader protocol

Use a small protocol so public orchestration can be tested with a fake reader:

```python
class StatementTextReader(Protocol):
    def read(self, source: StatementSource) -> StatementText:
        ...
```

The protocol return type and source type must be exact so fake test readers
satisfy mypy and Pyright structurally.

### 23.3 Initial implementation

Use one proven text extraction library, expected to be `pdfplumber`, with OCR
disabled.

Do not introduce multiple readers or fallback extraction chains until a real
fixture proves the need.

### 23.4 Source reading errors

Differentiate at least:

- source not found;
- source is not a regular file;
- unreadable source;
- invalid or corrupt PDF;
- encrypted PDF;
- no pages;
- no extractable text.

### 23.5 No network and no implicit OCR

The reader performs no network calls and does not silently send documents to an
OCR or cloud service.

---

## 24. Broker Detection

### 24.1 Separate broker identity from processor revision

Broker detection answers:

> Which institution produced this statement?

Processor matching answers:

> Which known grammar or revision owns this statement?

Keeping those questions separate produces clearer errors and reduces
cross-broker matching noise.

### 24.2 Detection rules

Detection uses strong document signatures such as:

- institution name;
- legally identifying footer text;
- account statement title; and
- broker-specific section labels.

Do not detect a broker from:

- filename;
- directory name;
- statement date alone;
- one common financial phrase; or
- user-provided hints without source confirmation.

### 24.3 Detection outcomes

```text
zero brokers matched
→ UnsupportedBrokerError

one broker matched
→ continue

multiple brokers matched
→ AmbiguousBrokerError
```

### 24.4 Testing

Broker detection tests include:

- positive TD signature;
- positive Schwab signature;
- unknown statement;
- mixed/ambiguous signatures;
- deterministic results independent of signature order.

---

## 25. Processor Contract

### 25.1 Protocol

The initial processor protocol should remain small:

```python
class StatementProcessor(Protocol):
    name: str
    broker: Broker

    def match(self, text: StatementText) -> ProcessorMatch:
        ...

    def parse(
        self,
        source: StatementSource,
        text: StatementText,
    ) -> ParsedStatement:
        ...
```

Do not add lifecycle hooks, inheritance hierarchies, plugin metadata, or
service containers until real processors prove they are necessary.

### 25.2 Processor properties

A processor must be:

- stateless or effectively immutable;
- deterministic;
- safe to reuse across calls;
- independent of file I/O;
- independent of registry order;
- explicit about the broker it owns; and
- uniquely named.

### 25.3 Processor naming

Names are stable format identifiers, for example:

```text
tdameritrade.monthly_2020
charlesschwab.schwab_one_2023
```

The year refers to the first confirmed grammar revision, not a promise that the
processor only accepts that calendar year.

A processor may parse many non-contiguous statement dates if they share the
same grammar.

### 25.4 Processor ownership

A processor owns:

- document layout recognition;
- required section discovery;
- section boundaries;
- table column interpretation;
- row wrapping behavior;
- composition of activity rules;
- zero-activity and zero-position proof; and
- construction of the normalized statement.

A processor does not own:

- PDF reading;
- global source hashing;
- public archive orchestration;
- historical facts that apply across processor revisions; or
- reconciliation mutations.

---

## 26. Processor Matching

### 26.1 Structured match result

Use:

```python
@dataclass(frozen=True, slots=True)
class ProcessorMatch:
    matched: bool
    confidence: int
    reason: str
```

Validation rules:

- confidence is between 0 and 100;
- an unmatched result uses confidence 0;
- a matched result uses positive confidence;
- reason is non-empty; and
- matching never raises merely because a processor does not own the source.

### 26.2 Matching evidence

A match should rely on a conjunction of stable layout signatures, such as:

- statement title;
- section heading set;
- summary labels;
- table column headers;
- revision-specific wording; and
- wrapping conventions.

Do not use the filename or account number.

### 26.3 Confidence policy

Confidence is not fuzzy machine learning. It is a deterministic statement of
signature specificity.

Suggested bands:

- 100: unique revision marker set;
- 90: exact known heading and column combination;
- 70: intentionally broad compatible fallback;
- 0: no match.

Processors should normally target exact high-confidence signatures.

### 26.4 No silent tie-breaking

The initial design should not include processor priority.

Selection uses highest confidence. If more than one processor has the same
highest matched confidence, raise `AmbiguousProcessorError`.

A priority field may be introduced later only if a real overlap proves it is
needed and the behavior is documented with fixtures. It must not become a way
to hide accidental overlapping processors.

---

## 27. Processor Registry

### 27.1 Registry responsibilities

The registry:

- stores an immutable processor tuple;
- validates unique processor names;
- filters processors by detected broker;
- evaluates matches;
- selects one highest-confidence processor;
- returns deterministic diagnostics; and
- raises explicit zero-match or ambiguity errors.

### 27.2 No decorator registration

Do not use import-time decorators or mutable global registries.

The default processor catalog should be explicit:

```python
DEFAULT_PROCESSORS = (
    TdAmeritradeMonthly2020Processor(),
    SchwabOne2023Processor(),
)

DEFAULT_REGISTRY = ProcessorRegistry(DEFAULT_PROCESSORS)
```

This makes processor inclusion visible, testable, and deterministic.

### 27.3 Registry outcomes

```text
no processors registered for detected broker
→ UnsupportedStatementError

processors registered, none matched
→ UnsupportedStatementError with match reasons

one highest-confidence match
→ select processor

multiple highest-confidence matches
→ AmbiguousProcessorError
```

### 27.4 Registry tests

Test at least:

- empty registry;
- duplicate names;
- processor from wrong broker ignored;
- one match selected;
- higher confidence selected;
- equal top confidence rejected;
- lower-confidence matches included in diagnostics;
- selection independent of registration order; and
- fake processors satisfy the protocol exactly.

---

## 28. Rules Versus Processors

This distinction is mandatory.

### 28.1 Add or improve a reusable rule when

The layout and section grammar remain the same, and the statement exposes
another occurrence of a known financial activity family.

Examples:

- buy or sell row;
- option contract description;
- cash transfer;
- interest;
- FDIC sweep;
- reverse split;
- cash in lieu;
- option expiration; or
- reorganization fee.

### 28.2 Add a new processor when

The source interpretation contract changes materially.

Examples:

- different summary layout;
- changed transaction columns;
- changed page or section structure;
- materially different row wrapping;
- changed positions table;
- revision-specific headings that require another section parser; or
- a change that would make the existing processor's fixtures harder to
  understand or less trustworthy.

### 28.3 Do not create cumulative processors

Avoid:

```text
processor_001 = base
processor_002 = base + options
processor_003 = base + options + reverse splits
```

when all statements share the same layout.

The processor composes activity rules. The rule handles activity grammar.

### 28.4 Initial rule organization

Begin with one cohesive `rules.py` per broker family.

Split into a `rules/` package only when independently reusable boundaries are
proven by size, duplication, or testing needs.

Do not create one file per regex.

### 28.5 Cross-broker sharing

Do not force cross-broker rule reuse prematurely. Similar economic activity may
have very different source grammar.

Extract a shared parser only after duplication is real and the shared contract
is clearer than the broker-specific versions.

---

## 29. Strict Section and Activity Parsing

### 29.1 Required section contract

Each processor documents the required sections for its grammar.

Missing required sections raise `MissingSectionError` or a more specific parse
error.

### 29.2 Candidate financial occurrences

A processor must identify every row or row cluster in a financial activity
section that is a candidate for normalization.

Each candidate occurrence must be:

- consumed by exactly one rule;
- deliberately grouped into a documented cluster; or
- rejected explicitly.

### 29.3 Rule outcomes

For one candidate occurrence:

```text
zero rules matched
→ UnsupportedActivityError

one rule matched
→ normalize

multiple rules matched
→ AmbiguousActivityError
```

### 29.4 Ignore behavior

Processors may ignore non-financial boilerplate only through narrow,
fixture-backed section logic.

Do not use broad catch-all patterns such as "ignore any line that does not
parse."

### 29.5 Complete statement validation

Before returning, a processor must prove:

- broker and processor identity;
- account identity;
- statement period;
- required sections;
- complete candidate activity consumption;
- closing positions or explicit zero-position proof;
- evidence linkage; and
- any format-specific required totals or summaries.

### 29.6 Inactive statements

No activity rows do not automatically prove zero activity.

The processor must find source evidence that the statement reports no activity
or zero activity totals for the relevant sections.

### 29.7 Zero positions

No positions table does not automatically prove zero positions.

Accept an empty positions tuple only when another reliable statement section
establishes zero holdings across every relevant security category.

---

## 30. Corporate-Action Clusters

### 30.1 One economic action, multiple rows

A broker may express one economic transformation through several rows.

Example:

```text
Delivered old security
Received replacement security
Mandatory reorganization fee
Cash in lieu
```

Do not interpret every row as an independent transformation.

### 30.2 Correlation

Use source correlation keys when available, such as a reorganization reference
number.

Otherwise, cluster only through deterministic evidence such as:

- same effective date;
- source and target identifiers;
- matching descriptions;
- compatible quantities; and
- processor-specific adjacency rules.

### 30.3 Normalized output

A cluster may produce several economic events, for example:

- reverse split;
- fee; and
- cash in lieu.

Each event may share overlapping evidence occurrences.

### 30.4 Reference catalog role

If the statement row does not contain enough information to establish the
ratio or transformation, consult explicit historical corporate-action
reference data.

Do not scatter special-case ratios through transaction parsing code.

### 30.5 Fractional economics

Preserve:

- exact transformed quantity;
- whole shares delivered;
- fractional entitlement; and
- cash paid for the fraction

when the source and reference facts support those values.

---

## 31. Historical Reference Data

### 31.1 Parsing grammar is not reference data

Use this classification test:

- "How is this row laid out?" → processor or rule.
- "What security did this historical identifier represent?" → reference data.
- "What dated transformation occurred?" → corporate-action reference data.
- "How does this broker classify the amount in a summary?" → reconciliation.

### 31.2 Security mappings

CUSIP and CINS mappings belong in one date-aware catalog.

Each added fact should include enough context to understand why it exists.

### 31.3 Corporate-action facts

Historical ratios, source-to-target symbol transformations, and effective dates
belong in `reference/corporate_actions.py`.

### 31.4 Reference-data tests

Every new historical fact receives tests for:

- exact identifier or security;
- applicable date range;
- successful resolution;
- non-applicable dates; and
- ambiguity detection where relevant.

### 31.5 Reference provenance

Where practical, record a concise note or external source citation in the code
or accompanying documentation.

The parser must not make a historical claim that cannot be explained later.

---

## 32. Reconciliation Architecture

### 32.1 Separation from parsing

Parsing determines what the source says and emits normalized economics.

Reconciliation checks whether those normalized economics agree with reported
statement facts.

Reconciliation must not rewrite events to make totals match.

### 32.2 Statement-level checks

Expected checks include:

- opening cash plus signed activity equals closing cash;
- normalized activity classifications match statement summaries;
- closing positions match statement-reported positions;
- corporate-action transformations explain quantity changes;
- reported account values are internally consistent where sufficient data is
  available; and
- zero activity and zero positions are properly proven.

### 32.3 Broker-specific summary semantics

Broker-specific classification belongs in reconciliation profiles, not domain
events.

Example:

If TD Ameritrade includes cash-in-lieu proceeds under `Securities Sold`, the TD
reconciliation classifier counts the normalized cash-in-lieu event in that
reported category.

It does not create a fake sale.

### 32.4 Reconciliation result model

A future result should be structured:

```python
class ReconciliationStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True, slots=True)
class ReconciliationCheck:
    name: str
    status: ReconciliationStatus
    expected: Decimal | None
    actual: Decimal | None
    difference: Decimal | None
    reason: str
```

Do not implement this model until the first real check is being added.

### 32.5 Strict default

A required failed reconciliation check raises a reconciliation exception from
the public parse flow.

Optional or unavailable checks are explicitly `NOT_APPLICABLE`; they are not
silently treated as passing.

---

## 33. Archive Processing and Continuity

### 33.1 Private smoke workflow first

Before publishing an archive API, use a private chronological smoke workflow
against the historical archive.

Example:

```text
[01/78] PASS
[02/78] PASS
...
[39/78] FAIL
```

### 33.2 Failure classification before code changes

Every failure is classified first as exactly one primary category:

1. new statement layout or processor;
2. reusable activity grammar;
3. security or historical reference fact;
4. reconciliation semantic rule; or
5. genuinely malformed or ambiguous source.

Do not edit code until the failure is classified.

### 33.3 Duplicate source handling

Archive processing identifies duplicate PDFs by SHA-256, not filename.

### 33.4 Ordering

After parsing, statements are ordered deterministically by:

- broker;
- account identifier;
- period start;
- period end; and
- source digest as a final stable key.

### 33.5 Cross-statement checks

Expected continuity checks include:

- account identity consistency;
- non-overlapping statement periods;
- opening cash matching prior closing cash;
- opening positions matching prior closing positions after known boundary
  activity;
- pending-to-settled trade correlation;
- migration-boundary transformations; and
- unexplained symbol or quantity discontinuities.

### 33.6 Public archive API later

Only expose `parse_archive()` after failure semantics, duplicate behavior,
partial-result behavior, and grouping rules are intentionally designed.

---

## 34. Exception and Diagnostic Design

### 34.1 Base exception

```python
class BrokerageStatementsError(Exception):
    """Base exception for package operational failures."""
```

### 34.2 Exception families

Expected exception families are:

#### Source and extraction

- `SourceNotFoundError`
- `InvalidSourceError`
- `SourceReadError`
- `InvalidPdfError`
- `EncryptedPdfError`
- `EmptyStatementTextError`

#### Broker and processor selection

- `UnsupportedBrokerError`
- `AmbiguousBrokerError`
- `DuplicateProcessorError`
- `UnsupportedStatementError`
- `AmbiguousProcessorError`

#### Parsing

- `StatementParseError`
- `MissingSectionError`
- `UnsupportedActivityError`
- `AmbiguousActivityError`
- `UnknownSecurityError`
- `AmbiguousSecurityError`
- `IncompleteStatementError`

#### Numeric and domain validation

- `InvalidDecimalError`

#### Reconciliation

- `ReconciliationError`
- `CashReconciliationError`
- `PositionReconciliationError`
- `SummaryReconciliationError`
- `ContinuityError`

Create each class only when behavior and tests are added.

### 34.3 Structured diagnostics

Operational parse exceptions should retain structured fields where relevant:

- source path or digest;
- broker;
- processor name;
- statement period;
- page;
- section;
- raw row or row cluster;
- rule candidates;
- match results; and
- human-readable reason.

Because `exceptions.py` must not import domain, use standard-library types and
strings in exception fields or define a domain-independent diagnostic record.

### 34.4 Human-readable rendering

An unsupported activity should render approximately:

```text
UnsupportedActivityError
processor: tdameritrade.monthly_2020
broker: tdameritrade
period: 2020-09-01..2020-09-30
page: 4
section: Account Activity
row: ...
reason: unknown Delivered - Other activity
```

### 34.5 Exception chaining

Wrap lower-level library errors with `raise ... from exc` when the original
cause is useful.

Do not expose third-party extraction exceptions directly through the public
API.

### 34.6 No automatic traceback suppression

The library raises exceptions normally. CLI or application integrations may
choose how to present tracebacks.

---

## 35. Determinism Rules

The following are mandatory:

- source identity uses raw-byte SHA-256;
- processor names are unique and stable;
- registry results are independent of insertion order;
- fixtures have stable expected ordering;
- events preserve source order;
- reference resolution is date-aware and deterministic;
- no network resolution occurs during parsing;
- no current date is used to interpret two-digit years;
- no locale-aware decimal parsing occurs implicitly;
- two-digit option years use an explicit processor rule;
- no timezone conversion is performed on date-only statement data;
- archive ordering uses documented stable keys; and
- error diagnostic lists are sorted deterministically.

---

## 36. Testing Strategy

### 36.1 Global quality gate

Every change must pass:

```text
make format-check
make lint
make typecheck
make coverage
make build
make check-dist
```

Release candidates additionally pass clean-wheel installation.

### 36.2 Coverage

Maintain 100% branch coverage.

Do not exclude meaningful production code merely to preserve the number.

Every new production module arrives with tests in the same change.

### 36.3 Test location

Tests live under top-level `tests/`, mirroring package areas.

### 36.4 Unit tests

Unit-test:

- domain invariants;
- decimal handling;
- broker detection;
- match result validation;
- registry selection;
- individual activity rules;
- reference resolution;
- reconciliation classification; and
- exception rendering.

### 36.5 Whole-statement processor tests

Every processor has sanitized whole-statement fixtures proving:

- positive ownership matching;
- rejection of neighboring revisions;
- account and period extraction;
- complete event output;
- positions;
- summaries and balances when required;
- evidence page and section coordinates;
- inactivity proof;
- zero-position proof; and
- unknown-row failure.

### 36.6 Golden expected results

Whole-statement expected results may use:

- explicit dataclass construction; or
- a deterministic test-only serialization format.

Do not add a public serialization API solely for fixtures.

### 36.7 Regression rule

Every production bug or newly supported source behavior results in:

```text
new sanitized fixture
+
new or changed processor/rule/reference/reconciliation behavior
+
all old fixtures unchanged
```

### 36.8 Negative fixtures

Maintain fixtures proving failure for:

- unsupported layout;
- ambiguous layout;
- unknown activity;
- unknown security;
- missing required section;
- unproven zero positions;
- malformed row; and
- reconciliation mismatch.

### 36.9 No network in tests

Tests use no network and no live brokerage services.

### 36.10 Private archive tests

The private historical archive may be exercised by a local smoke command or
private test configuration, but must not be required for public CI.

---

## 37. Fixture Policy and Privacy

### 37.1 Never commit real personal statements

Public fixtures must remove or replace:

- names;
- addresses;
- full account numbers;
- tax identifiers;
- contact details;
- barcodes and document IDs that expose personal data; and
- unrelated personal notes.

### 37.2 Preserve grammar while sanitizing

Sanitization must retain the source shape needed by the parser:

- line wrapping;
- table columns;
- minus signs;
- parentheses;
- decimal precision;
- section order; and
- correlation-key format.

### 37.3 Fixture classes

Use:

- whole-statement text fixtures for processors;
- small section or row fixtures for rules;
- expected-result data kept beside the relevant test; and
- private PDFs outside the repository for archive smoke testing.

### 37.4 Fixture manifest

Each processor fixture should document:

- sanitized fixture name;
- owning processor;
- broker;
- statement grammar/revision;
- behaviors exercised;
- origin category, without personal identifiers; and
- why a separate fixture is necessary.

---

## 38. Processor Stability and Versioning

### 38.1 Stable after proof

A processor becomes stable when it has:

- at least one complete whole-statement fixture;
- fixtures for every material variant it claims;
- positive and negative match tests;
- complete row-consumption tests;
- evidence tests;
- zero-position or inactivity tests where applicable; and
- a released package version.

### 38.2 Safe changes to an existing processor

Appropriate changes include:

- a bug fix that makes the implementation conform to its existing fixture-backed
  grammar;
- a new occurrence of the same row grammar;
- a reusable rule addition that does not alter existing interpretations;
- improved diagnostics; and
- performance changes with identical results.

### 38.3 New processor revision required

Prefer a new processor when supporting the source requires:

- different section boundaries;
- materially changed columns;
- incompatible wrapping assumptions;
- changed summary semantics embedded in layout parsing;
- altered position-table interpretation; or
- broad conditionals that make the old processor harder to trust.

### 38.4 Never delete historical support casually

Old processors may remain necessary indefinitely for historical statements.

Deprecation requires an explicit reason and a migration path. Removal is a
breaking change.

### 38.5 Processor name stability

Once released, a processor name is part of diagnostic and evidence identity.
Do not rename it casually.

---

## 39. Broker Implementation Plan: TD Ameritrade

### 39.1 First processor objective

Implement one proven TD Ameritrade monthly statement grammar before attempting
the entire archive.

The provisional processor name is:

```text
tdameritrade.monthly_2020
```

Confirm the name against the actual fixture grammar before release.

### 39.2 Required format coverage

The first complete processor should establish:

- broker and monthly-layout matching;
- account identity;
- statement period;
- account summary or portfolio summary;
- activity section boundaries;
- positions;
- explicit zero-position proof; and
- inactive or zero-activity proof when applicable.

### 39.3 Initial activity fixtures

Add behavior incrementally with fixtures for:

- basic stock buy;
- basic stock sell;
- pending trade;
- settled trade;
- external deposit;
- external withdrawal;
- FDIC sweep;
- IDA interest;
- option open;
- option close;
- option expiration;
- reverse split cluster;
- cash in lieu;
- mandatory reorganization fee;
- security transfer; and
- zero positions.

### 39.4 TD option grammar

The option-description rule must support:

```text
<UNDERLYING>
<MONTH>
<DAY>
<2-OR-4-DIGIT-YEAR>
<STRIKE>
<C|P|CALL|PUT>
TO OPEN|TO CLOSE
```

Two-digit years must use an explicit deterministic interpretation rule.

### 39.5 TD corporate-action cluster

The reverse-split fixture should prove:

- old security delivery;
- replacement receipt;
- exact transformed quantity;
- whole shares delivered;
- fractional entitlement;
- cash in lieu;
- fee event;
- correlation reference; and
- shared evidence.

### 39.6 TD completion gate

Do not claim TD support in README as available until at least one whole
statement parses completely through the public API and its supported behaviors
are listed accurately.

---

## 40. Broker Implementation Plan: Charles Schwab

### 40.1 First processor objective

Implement one proven Schwab One grammar after the processor framework and first
TD processor have validated the architecture.

The provisional name is:

```text
charlesschwab.schwab_one_2023
```

Create a separate `schwab_one_2025` processor only if fixtures prove a material
grammar revision.

### 40.2 Required format coverage

The first complete Schwab processor should establish:

- Schwab One matching;
- account identity;
- statement period;
- beginning and ending account values;
- transaction details;
- positions;
- inactive-month proof; and
- migration-boundary evidence where present.

### 40.3 Initial activity fixtures

Add fixtures for:

- ordinary trade;
- interest;
- external transfer;
- migration activity;
- reverse split;
- compact reverse-split representation;
- redemption cash in lieu;
- worthless-security adjustment;
- inactive month; and
- symbol transformation.

### 40.4 Known historical cases

The processor/reference design must support:

- UAVS compact reverse split and cash in lieu;
- PHMB worthless-security adjustment; and
- DWACW to DJTWW historical transformation.

### 40.5 Revision decision

If the 2025 statement requires materially different account-value discovery or
transaction-table interpretation, create a new processor revision rather than
turning the 2023 processor into a date-driven collection of branches.

---

## 41. Release and Milestone Plan

The original handoff expected `0.1.0` to contain the full architectural
foundation. In reality, `0.1.0` was intentionally used to establish the
package, CI, and publishing flow.

The milestone plan is therefore updated.

### 41.1 `0.1.0` — Package foundation — released

Completed:

- repository structure;
- package metadata;
- typed-package marker;
- quality gates;
- tests and coverage policy;
- CI;
- distributions;
- clean-wheel validation; and
- Trusted Publishing.

### 41.2 `0.2.0` — Parsing architecture foundation

Deliver:

- hardened domain models;
- source and evidence contracts;
- statement text models;
- deterministic PDF reader;
- source hashing;
- broker detection;
- processor protocol;
- match result;
- immutable processor registry;
- strict selection exceptions;
- public `parse_statement()` orchestration tested with fake processors; and
- no claim of real broker support unless a complete processor is included.

### 41.3 `0.3.0` — First TD Ameritrade processor

Deliver one complete fixture-backed TD monthly processor and the initial TD
activity grammar set.

### 41.4 `0.4.0` — First Schwab processor

Deliver one complete fixture-backed Schwab One processor and the initial
Schwab activity grammar set.

### 41.5 `0.5.0` — Historical archive validation

Run the private chronological archive, classify every failure, and add isolated
rules, reference facts, or processor revisions until supported scope is
complete.

Target:

```text
78 / 78 supported historical statements parse
```

This target applies to the known private archive, not every statement Schwab or
TD has ever issued.

### 41.6 `0.6.0` — Reconciliation

Deliver:

- opening and closing cash reconciliation;
- reported activity-summary reconciliation;
- closing-position reconciliation;
- corporate-action transformations;
- cross-statement continuity; and
- broker-specific summary classification.

### 41.7 `0.7.0` — Public API hardening

Deliver:

- finalized root exports;
- complete user documentation;
- supported-format matrix;
- exception documentation;
- stable examples; and
- archive API decision.

### 41.8 `1.0.0` criteria

Do not release 1.0 merely because the archive passes.

Require:

- stable public `parse_statement()` API;
- stable domain names and core field semantics;
- complete TD and Schwab format documentation;
- deterministic selection and parsing;
- strict reconciliation for supported formats;
- private historical archive passing;
- public sanitized fixtures for every claimed grammar;
- clear exception contracts;
- no known silent-skip paths;
- Python-version CI green;
- 100% branch coverage; and
- at least one downstream integration successfully using the package without
  importing processor internals.

---

## 42. Immediate Implementation Sequence

The next work should proceed in this order.

### Step 1 — Commit this blueprint

Add `BLUEPRINT.md` at the repository root and treat it as the architecture
contract.

### Step 2 — Finish and verify statement text models

Ensure page-aware text models and tests are complete and green.

### Step 3 — Harden the current domain

Implement the known corrections from Section 17:

1. central `Security` alias;
2. neutral symbol security name;
3. multiple evidence occurrences;
4. explicit transfer direction;
5. trade status and position effect;
6. corporate-action source and target security;
7. account identity;
8. processor identity;
9. statement currency; and
10. position evidence.

Do these as small, test-complete changes. Do not rewrite the whole domain in one
unreviewable commit.

### Step 4 — Expand exceptions only as needed

Add broker-detection and processor-selection exceptions with structured fields
and complete tests.

### Step 5 — Build processor base contract

Add:

```text
src/brokerage_statements/processors/base.py
tests/processors/test_base.py
```

Implement and test `ProcessorMatch` and `StatementProcessor`.

### Step 6 — Build broker detection

Add deterministic detection with fake statement text fixtures.

### Step 7 — Build immutable registry

Test zero matches, one match, confidence selection, ambiguity, duplicate names,
and registration-order independence.

### Step 8 — Build source hashing and PDF reader

Add the runtime PDF dependency only when the reader and tests are implemented.

### Step 9 — Build public orchestration with fakes

Prove the complete flow without real broker parsing:

```text
path → source → text → broker → processor → ParsedStatement
```

### Step 10 — Review the first real TD statements

Select a representative initial fixture set:

- ordinary active month;
- option activity month;
- corporate-action month; and
- zero-position or inactive month.

Only then implement the first real processor.

---

## 43. Definition of Done

### 43.1 Domain change

A domain change is done when:

- the invariant is clearly documented;
- names are broker-neutral;
- all branches are tested;
- `__all__` exports are intentional;
- Ruff passes;
- mypy passes;
- coverage remains 100%; and
- no broker-specific parsing text appears in domain code.

### 43.2 New activity rule

A rule is done when:

- the source grammar is documented in its test fixture;
- positive examples pass;
- malformed and near-match examples fail safely;
- rule ambiguity is tested;
- normalized output is exact;
- evidence is complete; and
- all existing processor fixtures remain unchanged.

### 43.3 New processor

A processor is done when:

- its grammar is named and documented;
- positive matching is fixture-backed;
- neighboring processors reject its fixture;
- all required sections are parsed;
- all candidate financial occurrences are consumed exactly once or clustered;
- unknown candidate rows fail;
- account, period, currency, events, and positions are complete;
- inactivity and zero-position cases are proven where relevant;
- evidence is complete;
- statement-level validation passes;
- 100% branch coverage remains; and
- README support claims are updated accurately.

### 43.4 Reference fact

A reference fact is done when:

- it is located outside parser grammar;
- it is date-aware where necessary;
- its reason is documented;
- resolution and non-resolution are tested; and
- it does not rewrite historical identity.

### 43.5 Reconciliation rule

A reconciliation rule is done when:

- it explains a documented broker summary semantic;
- it does not mutate normalized events;
- expected, actual, and difference are deterministic;
- pass and fail cases are tested; and
- the failure diagnostic identifies the relevant evidence.

### 43.6 Release

A release is done when:

- local `make release-check` passes;
- CI passes on Python 3.11–3.14;
- release tag matches package version;
- wheel and sdist pass Twine validation;
- `py.typed` is present;
- clean-wheel import succeeds;
- release notes state exactly what is and is not supported; and
- PyPI publication succeeds through Trusted Publishing.

---

## 44. Change Decision Trees

### 44.1 A statement does not parse

```text
Does the broker detection fail?
  ├─ yes → improve strong broker signatures or mark unsupported
  └─ no
      ↓
Does no processor match?
  ├─ yes → compare layout contract
  │        ├─ materially new layout → new processor
  │        └─ same layout → fix match signatures carefully
  └─ no
      ↓
Does a known section contain a new activity row?
  ├─ yes → reusable activity rule
  └─ no
      ↓
Is an identifier or historical transformation unknown?
  ├─ yes → reference data
  └─ no
      ↓
Do normalized events disagree only with broker summary categories?
  ├─ yes → reconciliation classification
  └─ no
      ↓
Is the source malformed or genuinely ambiguous?
  ├─ yes → fail explicitly
  └─ no → re-evaluate classification before changing architecture
```

### 44.2 Modify processor or create revision

```text
Can the change be explained as another occurrence of the same grammar?
  ├─ yes → improve rule or narrow processor logic
  └─ no
      ↓
Would the change alter section boundaries, columns, wrapping, or interpretation?
  ├─ yes → new processor revision
  └─ no
      ↓
Would existing fixtures become harder to understand or require date branches?
  ├─ yes → new processor revision
  └─ no → carefully update existing processor with a new fixture
```

### 44.3 Add abstraction or keep code local

```text
Is the behavior used by more than one proven caller?
  ├─ no → keep it local
  └─ yes
      ↓
Does extracting it make both callers easier to understand?
  ├─ no → keep duplication temporarily
  └─ yes → extract the smallest reusable contract
```

---

## 45. Anti-Patterns

Do not introduce:

### 45.1 Mega-parser

One broker class containing every layout revision, rule, mapping, and
reconciliation branch.

### 45.2 One processor per PDF

Processors belong to grammars, not filenames or archive positions.

### 45.3 Date-only routing

Statement date may support diagnostics, but a date alone does not prove layout
ownership.

### 45.4 Parser conditionals for historical facts

Avoid:

```python
if symbol == "UAVS" and statement_date == ...:
    ratio = ...
```

Use a dated corporate-action reference fact.

### 45.5 Symbol aliasing across transformations

Do not treat `DWACW` and `DJTWW` as the same timeless symbol.

### 45.6 Silent unknown-row skipping

No catch-all `continue` after a row fails to parse.

### 45.7 Reconciliation by fabrication

No fake trade or balancing cash event solely to match a summary.

### 45.8 Global mutable registry

No import-order-dependent decorators or runtime processor mutation.

### 45.9 Generic service hierarchy

No `BaseService`, compiler layers, repositories, managers, or dependency
containers without a proven need.

### 45.10 Premature tiny-file explosion

Prefer one cohesive `rules.py` over seven one-regex modules.

### 45.11 Shipping private statements

Never commit unsanitized PDFs or text extracts.

### 45.12 Public API leakage

Users should not need to instantiate a registry or processor to parse an
ordinary supported statement.

---

## 46. Security, Privacy, and Operational Behavior

### 46.1 Local processing

Parsing is local and performs no network calls.

### 46.2 No automatic logging configuration

The package must not configure root logging.

If internal logging is later added, use a package logger and emit no raw
statement text at normal levels.

### 46.3 Raw diagnostic sensitivity

Raw rows may contain financial or personal information. Callers decide whether
to display or persist full diagnostics.

### 46.4 Temporary files

Avoid temporary files when the PDF library can read the original source.

If temporary files become necessary, use secure temporary directories and
clean them deterministically.

### 46.5 No executable document content

The package extracts text only. It does not execute embedded scripts, launch
attachments, or follow links from PDFs.

---

## 47. Performance Guidelines

Correctness and determinism come before throughput.

Initial expectations:

- read each source once;
- calculate SHA-256 in a streaming manner;
- extract text once;
- match processors without full parsing;
- parse one statement sequentially;
- avoid repeated whole-document regex passes where a page or section boundary
  is available; and
- do not cache globally until profiling proves a need.

Archive parallelism may be added later, but output order and failure semantics
must remain deterministic.

---

## 48. Documentation Plan

### 48.1 `README.md`

Keep user-facing and truthful.

Add sections only when behavior exists:

1. badges and purpose;
2. design goals;
3. installation;
4. quick start;
5. supported brokers and formats;
6. strict failure behavior;
7. development; and
8. license.

### 48.2 `BLUEPRINT.md`

Architecture and implementation source of truth.

### 48.3 Processor support matrix

Once real processors exist, document:

| Broker | Processor | Format | Supported | Notes |
| --- | --- | --- | --- | --- |
| TD Ameritrade | `tdameritrade.monthly_2020` | Monthly | Yes | Fixture-backed |
| Schwab | `charlesschwab.schwab_one_2023` | Schwab One | Yes | Fixture-backed |

Only list support that is tested through the public API.

### 48.4 Release notes

State:

- new processors;
- new activity grammars;
- new reference facts;
- reconciliation changes;
- public API changes;
- known limitations; and
- whether historical outputs changed.

### 48.5 Architecture decisions

Major changes may be recorded in a future `docs/decisions/` directory when the
first decision cannot be explained clearly inside this blueprint.

Do not create the directory before that need exists.

---

## 49. Code and Review Standards

Apply the full Python coding standards:

- PEP 8;
- Ruff;
- 79-character Python line length;
- strict typing;
- explicit readable code;
- module path docstrings;
- focused modules;
- meaningful names;
- tests for all non-trivial behavior;
- no giant classes or functions;
- no ignored lint errors without a documented reason; and
- CI as a merge gate.

Every Python source module begins with:

```python
"""
src/brokerage_statements/<path>.py

Concise module responsibility.
"""
```

Test modules follow the same convention with their repository-relative path.

---

## 50. Blueprint Maintenance

Review this blueprint at these points:

- before beginning the first real processor;
- after the first TD processor is complete;
- after the first Schwab processor is complete;
- before publishing an archive API;
- before introducing sophisticated reconciliation; and
- before 1.0.

Update it when a real source proves an assumption wrong.

Do not update it merely to describe speculative ideas.

The blueprint is successful when a future development session can begin by
reading it and confidently answer:

- where a change belongs;
- which tests and fixtures are required;
- what must remain stable; and
- what not to build.

---

# Appendix A — Proposed Foundation Contracts

These sketches communicate intended contracts. They are not instructions to
create every class immediately.

## A.1 Security identity

```python
class OptionRight(StrEnum):
    CALL = "call"
    PUT = "put"


@dataclass(frozen=True, slots=True)
class SymbolSecurity:
    symbol: str


@dataclass(frozen=True, slots=True)
class OptionSecurity:
    underlying: str
    expiration: date
    right: OptionRight
    strike: Decimal


Security = SymbolSecurity | OptionSecurity
```

## A.2 Evidence

```python
@dataclass(frozen=True, slots=True)
class StatementSource:
    path: Path
    sha256: str


@dataclass(frozen=True, slots=True)
class SourceEvidence:
    source: StatementSource
    page: int | None = None
    section: str | None = None
    raw_text: str | None = None
    processor: str | None = None
    reference: str | None = None
    sequence: int | None = None


Evidence = tuple[SourceEvidence, ...]
```

## A.3 Trade semantics

```python
class TradeSide(StrEnum):
    BUY = "buy"
    SELL = "sell"


class TradeStatus(StrEnum):
    PENDING = "pending"
    SETTLED = "settled"


class PositionEffect(StrEnum):
    OPEN = "open"
    CLOSE = "close"


@dataclass(frozen=True, slots=True)
class TradeEvent:
    date: date
    settlement_date: date | None
    security: Security
    side: TradeSide
    status: TradeStatus
    position_effect: PositionEffect | None
    quantity: Decimal
    price: Decimal
    amount: Decimal
    evidence: Evidence
```

## A.4 Corporate action semantics

```python
@dataclass(frozen=True, slots=True)
class CorporateActionEvent:
    date: date
    action_type: CorporateActionType
    source_security: Security
    target_security: Security | None
    quantity_before: Decimal | None
    quantity_after: Decimal | None
    cash: Decimal | None
    evidence: Evidence
```

## A.5 Processor matching

```python
@dataclass(frozen=True, slots=True)
class ProcessorMatch:
    matched: bool
    confidence: int
    reason: str


class StatementProcessor(Protocol):
    name: str
    broker: Broker

    def match(self, text: StatementText) -> ProcessorMatch:
        ...

    def parse(
        self,
        source: StatementSource,
        text: StatementText,
    ) -> ParsedStatement:
        ...
```

---

# Appendix B — Exception Matrix

| Stage | Condition | Exception family |
| --- | --- | --- |
| Source | Path absent | `SourceNotFoundError` |
| Source | Not a regular readable file | `InvalidSourceError` |
| PDF | Corrupt or unsupported PDF | `InvalidPdfError` |
| PDF | Encrypted PDF | `EncryptedPdfError` |
| PDF | No meaningful text | `EmptyStatementTextError` |
| Detection | No broker signatures | `UnsupportedBrokerError` |
| Detection | More than one broker | `AmbiguousBrokerError` |
| Registry | Duplicate processor name | `DuplicateProcessorError` |
| Registry | No processor match | `UnsupportedStatementError` |
| Registry | Equal top matches | `AmbiguousProcessorError` |
| Parsing | Required section absent | `MissingSectionError` |
| Parsing | No rule owns activity | `UnsupportedActivityError` |
| Parsing | Multiple rules own activity | `AmbiguousActivityError` |
| Security | No historical resolution | `UnknownSecurityError` |
| Security | Multiple historical resolutions | `AmbiguousSecurityError` |
| Parsing | Statement incomplete | `IncompleteStatementError` |
| Reconcile | Cash mismatch | `CashReconciliationError` |
| Reconcile | Position mismatch | `PositionReconciliationError` |
| Reconcile | Summary mismatch | `SummaryReconciliationError` |
| Archive | Cross-period mismatch | `ContinuityError` |

---

# Appendix C — Fixture Manifest Template

```markdown
## Fixture: tdameritrade/monthly_2020/reverse_split.txt

- Broker: TD Ameritrade
- Owning processor: `tdameritrade.monthly_2020`
- Source type: Sanitized whole-statement text
- Statement grammar: Monthly layout
- Behaviors:
  - Delivered old security
  - Received replacement security
  - Reverse split
  - Fractional entitlement
  - Cash in lieu
  - Reorganization fee
- Match markers:
  - ...
- Required sections:
  - ...
- Sanitization notes:
  - Names and account values replaced
  - Row wrapping preserved
- Reason this fixture is separate:
  - Proves corporate-action cluster behavior
```

---

# Appendix D — Processor Support Checklist

```text
[ ] Unique stable processor name
[ ] Broker enum assigned
[ ] Positive match fixture
[ ] Negative neighboring-format fixture
[ ] Match confidence documented
[ ] Account identifier parsed
[ ] Statement period parsed
[ ] Currency established
[ ] Required sections validated
[ ] Activity candidates fully consumed
[ ] Unknown activity fails
[ ] Ambiguous rule fails
[ ] Events preserve source order
[ ] Every event has evidence
[ ] Positions parsed or zero positions proven
[ ] Inactive statement behavior proven
[ ] Summary/balance facts parsed where required
[ ] Reconciliation checks pass where implemented
[ ] 100% branch coverage
[ ] Strict mypy passes
[ ] Ruff passes
[ ] Public API test passes
[ ] README support matrix updated
[ ] Release notes prepared
```

---

# Appendix E — Archive Failure Record Template

```markdown
## Failure

- Archive position: 39 / 78
- Source digest: ...
- Broker: ...
- Statement period: ...
- Selected processor: ...
- Failure exception: ...
- Page and section: ...
- Raw occurrence: ...

## Classification

Choose one:

1. New statement layout / processor
2. Reusable activity grammar
3. Security or historical reference fact
4. Reconciliation semantic rule
5. Malformed or genuinely ambiguous source

## Decision

- Existing processor changed: yes / no
- New processor added: yes / no
- Rule added: yes / no
- Reference fact added: yes / no
- Reconciliation rule added: yes / no

## Regression Proof

- New sanitized fixture: ...
- Existing processor fixtures unchanged: yes / no
- Coverage: 100%
- Notes: ...
```

---

# Appendix F — Final Architectural Test

Before merging any package architecture change, answer all five questions:

1. Does this make the next unknown statement easier to support?
2. Does it leave already-supported processors easier to trust?
3. Is the behavior located in parsing grammar, reference data, or
   reconciliation correctly?
4. Is every successful normalized result auditable to source evidence?
5. Would an unsupported or ambiguous source fail loudly rather than look
   successful?

If any answer is no, revise the design before merging.
