"""
tests/processors/tdameritrade/activity/test_activity.py

Tests for TD Ameritrade account-activity orchestration.
"""

from __future__ import annotations

import pytest

from brokerage_statements.domain import (
    CashTransferEvent,
    IncomeEvent,
    TradeEvent,
)
from brokerage_statements.exceptions import UnknownActivityError
from brokerage_statements.processors.tdameritrade.activity import (
    parse_activity,
)
from brokerage_statements.text import StatementPage

from ._helpers import (
    PROCESSOR_NAME,
    make_sections,
    make_source,
    parse_page,
    symbol_of,
)


def test_parse_activity_preserves_source_row_sequence() -> None:
    """Evidence sequence should reflect source activity-row order."""
    events = parse_page(
        "Account Activity\n"
        "03/17/20 03/17/20 Cash Journal - Other "
        "MOVE CASH BALANCE TO MARGIN "
        "- - 0.00 (2,000.00) 0.00\n"
        "03/19/20 03/20/20 Cash Buy - Securities Purchased "
        "DIREXION SHARES ETF TRUST NUGT "
        "200 5.52 (1,104.00) (104.00)"
    )

    assert len(events) == 1

    event = events[0]

    assert isinstance(event, TradeEvent)
    assert event.evidence[0].sequence == 2


def test_parse_activity_preserves_order_across_pages() -> None:
    """Different activity parsers should retain statement order."""
    first = StatementPage(
        number=5,
        text=(
            "Account Activity\n"
            "03/19/20 03/20/20 Cash Buy - Securities Purchased "
            "DIREXION SHARES ETF TRUST NUGT "
            "200 5.52 (1,104.00) (104.00)"
        ),
    )
    second = StatementPage(
        number=6,
        text=(
            "Account Activity\n"
            "03/20/20 03/23/20 Cash - Funds Deposited "
            "ACH IN - - 0.00 1,000.00 1,000.00"
        ),
    )
    third = StatementPage(
        number=7,
        text=(
            "Account Activity\n"
            "03/31/20 03/31/20 Cash Div/Int - Income "
            "INTEREST CREDIT - - 0.00 0.02 1,000.02"
        ),
    )

    events = parse_activity(
        make_source(),
        make_sections(first, second, third),
        processor_name=PROCESSOR_NAME,
    )

    assert len(events) == 3

    trade = events[0]
    deposit = events[1]
    income = events[2]

    assert isinstance(trade, TradeEvent)
    assert isinstance(deposit, CashTransferEvent)
    assert isinstance(income, IncomeEvent)

    assert symbol_of(trade.security) == "NUGT"

    assert trade.evidence[0].sequence == 1
    assert deposit.evidence[0].sequence == 2
    assert income.evidence[0].sequence == 3


def test_parse_activity_preserves_evidence_metadata() -> None:
    """Dispatcher-created evidence should preserve source metadata."""
    events = parse_page(
        "Account Activity\n"
        "03/19/20 03/20/20 Cash Buy - Securities Purchased "
        "DIREXION SHARES ETF TRUST NUGT "
        "200 5.52 (1,104.00) (104.00)",
        page_number=8,
    )

    assert len(events) == 1

    event = events[0]

    assert isinstance(event, TradeEvent)

    evidence = event.evidence[0]

    assert evidence.source == make_source()
    assert evidence.page == 8
    assert evidence.section == "Account Activity"
    assert evidence.processor == PROCESSOR_NAME
    assert evidence.sequence == 1


def test_parse_activity_allows_no_rows() -> None:
    """Activity sections without transaction rows should return no events."""
    events = parse_page(
        "Account Activity\nTrade Date Settle Date\nClosing Balance $0.00"
    )

    assert events == ()


def test_parse_activity_rejects_unknown_activity() -> None:
    """Unknown activity should fail rather than disappear."""
    row = (
        "03/20/20 03/20/20 Cash Mystery - Other "
        "UNSUPPORTED ACTIVITY - - 0.00 10.00 10.00"
    )

    with pytest.raises(
        UnknownActivityError,
        match="Unknown TD Ameritrade account activity",
    ):
        parse_page(f"Account Activity\n{row}")
