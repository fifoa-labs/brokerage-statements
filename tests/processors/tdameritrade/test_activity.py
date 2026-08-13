"""
tests/processors/tdameritrade/test_activity.py

Tests for TD Ameritrade settled account-activity parsing.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from brokerage_statements.domain import (
    CashTransferEvent,
    CashTransferType,
    FeeEvent,
    IncomeEvent,
    IncomeType,
    Security,
    SecurityTransferDirection,
    SecurityTransferEvent,
    StatementSource,
    SymbolSecurity,
    TradeEvent,
    TradeSide,
    TradeStatus,
)
from brokerage_statements.exceptions import (
    UnknownActivityError,
    UnresolvedSecurityError,
)
from brokerage_statements.processors.tdameritrade.activity import (
    parse_activity,
)
from brokerage_statements.processors.tdameritrade.sections import (
    StatementSections,
)
from brokerage_statements.text import StatementPage

PROCESSOR_NAME = "tdameritrade.monthly_2020"


def symbol_of(security: Security) -> str:
    """Return the symbol for a symbol-backed security."""
    assert isinstance(security, SymbolSecurity)
    return security.symbol


def make_source() -> StatementSource:
    """Return reusable statement source identity."""
    return StatementSource(
        path=Path("statement.pdf"),
        sha256="abc123",
    )


def make_sections(
    *pages: StatementPage,
) -> StatementSections:
    """Return statement sections containing account-activity pages."""
    summary = StatementPage(
        number=3,
        text="Portfolio Summary",
    )
    positions = StatementPage(
        number=4,
        text="Account Positions",
    )

    return StatementSections(
        summary=(summary,),
        positions=(positions,),
        activity=pages,
        pending=(),
    )


def parse_page(
    text: str,
    *,
    page_number: int = 5,
) -> tuple[
    TradeEvent
    | CashTransferEvent
    | IncomeEvent
    | FeeEvent
    | SecurityTransferEvent,
    ...,
]:
    """Parse one synthetic account-activity page."""
    page = StatementPage(
        number=page_number,
        text=text,
    )

    return parse_activity(
        make_source(),
        make_sections(page),
        processor_name=PROCESSOR_NAME,
    )


def test_parse_activity_preserves_settled_buy() -> None:
    """Settled purchases should normalize into buy trades."""
    events = parse_page(
        "Account Activity\n03/19/20 03/20/20 Cash Buy - Securities Purchased DIREXION SHARES ETF TRUST NUGT 200 5.52 (1,104.00) (104.00)"  # noqa: E501
    )

    assert len(events) == 1

    event = events[0]

    assert isinstance(event, TradeEvent)
    assert event.date == date(2020, 3, 19)
    assert event.settlement_date == date(2020, 3, 20)
    assert symbol_of(event.security) == "NUGT"
    assert event.side is TradeSide.BUY
    assert event.status is TradeStatus.SETTLED
    assert event.quantity == Decimal("200")
    assert event.price == Decimal("5.52")
    assert event.amount == Decimal("1104.00")
    assert event.position_effect is None

    assert len(event.evidence) == 1

    evidence = event.evidence[0]

    assert evidence.source == make_source()
    assert evidence.page == 5
    assert evidence.section == "Account Activity"
    assert evidence.processor == PROCESSOR_NAME
    assert evidence.sequence == 1


def test_parse_activity_preserves_settled_sell() -> None:
    """Settled sales should normalize quantity as a magnitude."""
    events = parse_page(
        "Account Activity\n03/23/20 03/25/20 Cash Sell - Securities Sold DIREXION SHARES ETF TRUST JNUG 1,000- 4.14 4,139.79 3,320.79"  # noqa: E501
    )

    assert len(events) == 1

    event = events[0]

    assert isinstance(event, TradeEvent)
    assert symbol_of(event.security) == "JNUG"
    assert event.side is TradeSide.SELL
    assert event.status is TradeStatus.SETTLED
    assert event.quantity == Decimal("1000")
    assert event.price == Decimal("4.14")
    assert event.amount == Decimal("4139.79")
    assert event.date == date(2020, 3, 23)
    assert event.settlement_date == date(2020, 3, 25)


def test_parse_activity_emits_regulatory_fee_with_sale() -> None:
    """Regulatory fees should remain separate normalized events."""
    events = parse_page(
        "Account Activity\n03/23/20 03/25/20 Cash Sell - Securities Sold DIREXION SHARES ETF TRUST JNUG 1,000- 4.14 4,139.79 3,320.79\nRegulatory Fee 0.21"  # noqa: E501
    )

    assert len(events) == 2

    trade = events[0]
    fee = events[1]

    assert isinstance(trade, TradeEvent)
    assert isinstance(fee, FeeEvent)

    assert symbol_of(trade.security) == "JNUG"
    assert fee.date == date(2020, 3, 25)
    assert fee.amount == Decimal("0.21")
    assert fee.description == "Regulatory Fee"

    assert trade.evidence == fee.evidence
    assert trade.evidence[0].sequence == 1


def test_parse_activity_joins_wrapped_trade_description() -> None:
    """Wrapped TD descriptions should form one logical activity row."""
    events = parse_page(
        "Account Activity\n03/24/20 03/26/20 Cash Buy - Securities Purchased BARCLAYS BANK PLC VXX 100 44.73 (4,473.00) (4,019.36)\nIPATH B SHRT TRM ETN"  # noqa: E501
    )

    assert len(events) == 1

    event = events[0]

    assert isinstance(event, TradeEvent)
    assert symbol_of(event.security) == "VXX"
    assert event.quantity == Decimal("100")
    assert event.price == Decimal("44.73")
    assert event.amount == Decimal("4473.00")
    raw_text = event.evidence[0].raw_text

    assert raw_text is not None
    assert "IPATH B SHRT TRM ETN" in raw_text


def test_parse_activity_preserves_external_deposit() -> None:
    """External funds deposited should become cash transfers."""
    events = parse_page(
        "Account Activity\n03/16/20 03/17/20 Cash - Funds Deposited ELECTRONIC FUNDING - - $ 0.00 $ 2,000.00 2,000.00"  # noqa: E501
    )

    assert len(events) == 1

    event = events[0]

    assert isinstance(event, CashTransferEvent)
    assert event.date == date(2020, 3, 17)
    assert event.transfer_type is CashTransferType.DEPOSIT
    assert event.amount == Decimal("2000.00")
    assert event.evidence[0].sequence == 1


def test_parse_activity_preserves_margin_deposit() -> None:
    """External deposits may be reported under margin account type."""
    events = parse_page(
        "Account Activity\n03/16/20 03/17/20 Margin - Funds Deposited ACH IN - - 0.00 1,000.00 1,000.00"  # noqa: E501
    )

    assert len(events) == 1

    event = events[0]

    assert isinstance(event, CashTransferEvent)
    assert event.transfer_type is CashTransferType.DEPOSIT
    assert event.amount == Decimal("1000.00")


def test_parse_activity_preserves_cash_award() -> None:
    """Cash awards reported as deposited funds should remain deposits."""
    events = parse_page(
        "Account Activity\n03/30/20 03/30/20 Cash Journal - Funds Deposited Cash Award - - 0.00 100.00 100.00"  # noqa: E501
    )

    assert len(events) == 1

    event = events[0]

    assert isinstance(event, CashTransferEvent)
    assert event.transfer_type is CashTransferType.DEPOSIT
    assert event.amount == Decimal("100.00")


def test_parse_activity_preserves_funds_disbursed() -> None:
    """External funds disbursed should become withdrawals."""
    events = parse_page(
        "Account Activity\n11/06/23 11/06/23 Cash Journal - Funds Disbursed TDA TO CS&CO TRANSFER - - 0.00 (414.71) 0.00"  # noqa: E501
    )

    assert len(events) == 1

    event = events[0]

    assert isinstance(event, CashTransferEvent)
    assert event.date == date(2023, 11, 6)
    assert event.transfer_type is CashTransferType.WITHDRAWAL
    assert event.amount == Decimal("414.71")


def test_parse_activity_preserves_interest_income() -> None:
    """Interest credits should normalize as interest income."""
    events = parse_page(
        "Account Activity\n09/30/21 09/30/21 Cash Div/Int - Income INTEREST CREDIT Payable: 09/30/2021 - - 0.00 0.02 2,887.83"  # noqa: E501
    )

    assert len(events) == 1

    event = events[0]

    assert isinstance(event, IncomeEvent)
    assert event.date == date(2021, 9, 30)
    assert event.income_type is IncomeType.INTEREST
    assert event.amount == Decimal("0.02")


def test_parse_activity_preserves_external_security_delivery() -> None:
    """Migration deliveries should become outgoing security transfers."""
    events = parse_page(
        "Account Activity\n11/06/23 11/06/23 Cash Delivered - Other PHARMACOM BIOVET INC PHMB 2,000,000- 0.00 - 414.71\nCOM\nTDA TO CS&CO TRANSFER 4981195781"  # noqa: E501
    )

    assert len(events) == 1

    event = events[0]

    assert isinstance(event, SecurityTransferEvent)
    assert event.date == date(2023, 11, 6)
    assert symbol_of(event.security) == "PHMB"
    assert event.direction is SecurityTransferDirection.OUT
    assert event.quantity == Decimal("2000000")


def test_parse_activity_preserves_external_security_receipt() -> None:
    """External receipts should become incoming security transfers."""
    events = parse_page(
        "Account Activity\n03/19/20 03/19/20 Cash Received - Other TEST SECURITY TEST 300 0.00 - 0.00\nEXTERNAL TRANSFER"  # noqa: E501
    )

    assert len(events) == 1

    event = events[0]

    assert isinstance(event, SecurityTransferEvent)
    assert symbol_of(event.security) == "TEST"
    assert event.direction is SecurityTransferDirection.IN
    assert event.quantity == Decimal("300")


@pytest.mark.parametrize(
    "row",
    [
        (
            "03/17/20 03/17/20 Cash Journal - Other "
            "MOVE CASH BALANCE TO MARGIN "
            "- - 0.00 (2,000.00) 0.00"
        ),
        (
            "03/23/20 03/23/20 Cash Journal - Other "
            "PURCHASE FDIC INSURED DEPOSIT ACCOUNT "
            "- - 0.00 (2,500.00) 0.00"
        ),
        (
            "03/20/20 03/20/20 Cash Journal - Other "
            "REDEMPTION FDIC INSURED DEPOSIT ACCOUNT "
            "- - 0.00 1,220.00 0.00"
        ),
        (
            "03/19/20 03/19/20 Cash Journal - Other "
            "TRANSFER FROM 498-119578-2 "
            "TO 498-119578-1 "
            "- - 0.00 1,000.00 1,000.00"
        ),
    ],
)
def test_parse_activity_ignores_known_internal_cash_journals(
    row: str,
) -> None:
    """Known internal cash movements should not create events."""
    events = parse_page(f"Account Activity\n{row}")

    assert events == ()


def test_parse_activity_ignores_internal_security_receipt() -> None:
    """Transfers between TD subaccounts should not become external events."""
    events = parse_page(
        "Account Activity\n03/19/20 03/19/20 Cash Received - Other DIREXION SHARES ETF TRUST NUGT 300 0.00 - 0.00\nDLY GOLD INDX 3X ETF\nTRANSFER FROM 498-119578-2"  # noqa: E501
    )

    assert events == ()


def test_parse_activity_ignores_internal_security_delivery() -> None:
    """Security delivered to another TD subaccount is internal."""
    events = parse_page(
        "Account Activity\n03/19/20 03/19/20 Margin Delivered - Other DIREXION SHARES ETF TRUST NUGT 300- 0.00 - 1,000.00\nDLY GOLD INDX 3X ETF\nTRANSFER TO 498-119578-1"  # noqa: E501
    )

    assert events == ()


def test_parse_activity_preserves_source_row_sequence() -> None:
    """Evidence sequence should reflect source activity-row order."""
    events = parse_page(
        "Account Activity\n03/17/20 03/17/20 Cash Journal - Other MOVE CASH BALANCE TO MARGIN - - 0.00 (2,000.00) 0.00\n03/19/20 03/20/20 Cash Buy - Securities Purchased DIREXION SHARES ETF TRUST NUGT 200 5.52 (1,104.00) (104.00)"  # noqa: E501
    )

    assert len(events) == 1

    event = events[0]

    assert isinstance(event, TradeEvent)

    # Row 1 was intentionally consumed as an internal journal.
    assert event.evidence[0].sequence == 2


def test_parse_activity_preserves_order_across_pages() -> None:
    """Activity events should remain ordered across statement pages."""
    first = StatementPage(
        number=5,
        text="Account Activity\n03/19/20 03/20/20 Cash Buy - Securities Purchased DIREXION SHARES ETF TRUST NUGT 200 5.52 (1,104.00) (104.00)\npage 3 of 9",  # noqa: E501
    )
    second = StatementPage(
        number=6,
        text="Account Activity\n03/23/20 03/25/20 Cash Sell - Securities Sold DIREXION SHARES ETF TRUST JNUG 1,000- 4.14 4,139.79 3,320.79\npage 4 of 9",  # noqa: E501
    )

    events = parse_activity(
        make_source(),
        make_sections(first, second),
        processor_name=PROCESSOR_NAME,
    )

    assert len(events) == 2

    first_event = events[0]
    second_event = events[1]

    assert isinstance(first_event, TradeEvent)
    assert isinstance(second_event, TradeEvent)

    assert symbol_of(first_event.security) == "NUGT"
    assert symbol_of(second_event.security) == "JNUG"

    assert first_event.evidence[0].page == 5
    assert second_event.evidence[0].page == 6

    assert first_event.evidence[0].sequence == 1
    assert second_event.evidence[0].sequence == 2


def test_parse_activity_ignores_page_footer_inside_row() -> None:
    """TD page footers should not contaminate source evidence."""
    events = parse_page(
        "Account Activity\n03/19/20 03/20/20 Cash Buy - Securities Purchased DIREXION SHARES ETF TRUST NUGT 200 5.52 (1,104.00) (104.00)\npage 3 of 9"  # noqa: E501
    )

    assert len(events) == 1

    event = events[0]

    assert isinstance(event, TradeEvent)
    raw_text = event.evidence[0].raw_text

    assert raw_text is not None
    assert "page 3 of 9" not in raw_text


def test_parse_activity_stops_row_at_closing_balance() -> None:
    """Closing-balance text should not become part of activity evidence."""
    events = parse_page(
        "Account Activity\n09/30/21 09/30/21 Cash Div/Int - Income INTEREST CREDIT - - 0.00 0.02 2,887.83\nClosing Balance $2,887.83\nUnrelated text after activity"  # noqa: E501
    )

    assert len(events) == 1

    event = events[0]

    assert isinstance(event, IncomeEvent)
    raw_text = event.evidence[0].raw_text

    assert raw_text is not None
    assert "Closing Balance" not in raw_text
    assert "Unrelated text" not in raw_text


def test_parse_activity_allows_no_rows() -> None:
    """An activity section with no transaction rows should be empty."""
    events = parse_page(
        "Account Activity\nTrade Date Settle Date\nClosing Balance $0.00"
    )

    assert events == ()


def test_parse_activity_rejects_unknown_activity() -> None:
    """Unknown activity should fail loudly rather than disappear."""
    row = (
        "03/20/20 03/20/20 Cash Mystery - Other "
        "UNSUPPORTED ACTIVITY - - 0.00 10.00 10.00"
    )

    with pytest.raises(
        UnknownActivityError,
        match="Unknown TD Ameritrade account activity",
    ):
        parse_page(f"Account Activity\n{row}")


def test_parse_activity_rejects_unknown_internal_journal() -> None:
    """Unknown journal semantics should not be silently ignored."""
    row = (
        "03/20/20 03/20/20 Cash Journal - Other "
        "UNRECOGNIZED INTERNAL ACTION "
        "- - 0.00 10.00 10.00"
    )

    with pytest.raises(
        UnknownActivityError,
        match="Unknown TD Ameritrade account activity",
    ):
        parse_page(f"Account Activity\n{row}")


def test_parse_activity_rejects_malformed_trade() -> None:
    """Recognized trade rows with invalid tails should fail loudly."""
    row = "03/19/20 03/20/20 Cash Buy - Securities Purchased BROKEN TRADE ROW"

    with pytest.raises(
        UnknownActivityError,
        match="Unable to parse TD Ameritrade trade row",
    ):
        parse_page(f"Account Activity\n{row}")


def test_parse_activity_rejects_malformed_cash_transfer() -> None:
    """Recognized cash transfers should require amount data."""
    row = "03/16/20 03/17/20 Cash - Funds Deposited BROKEN CASH TRANSFER"

    with pytest.raises(
        UnknownActivityError,
        match="Unable to parse TD Ameritrade cash transfer row",
    ):
        parse_page(f"Account Activity\n{row}")


def test_parse_activity_rejects_malformed_security_transfer() -> None:
    """Recognized security transfers should require security data."""
    row = "11/06/23 11/06/23 Cash Delivered - Other BROKEN SECURITY TRANSFER"

    with pytest.raises(
        UnknownActivityError,
        match="Unable to parse TD Ameritrade security transfer row",
    ):
        parse_page(f"Account Activity\n{row}")


def test_parse_activity_rejects_malformed_income() -> None:
    """Recognized income rows should require amount data."""
    row = "09/30/21 09/30/21 Cash Div/Int - Income BROKEN INCOME"

    with pytest.raises(
        UnknownActivityError,
        match="Unable to parse TD Ameritrade income row",
    ):
        parse_page(f"Account Activity\n{row}")


def test_parse_activity_resolves_uso_cusip() -> None:
    """USO trades should resolve TD's reverse-split CUSIP annotation."""
    events = parse_page(
        "\n".join(  # noqa: FLY002
            (
                "Account Activity",
                (
                    "04/02/20 04/06/20 Cash Sell - Securities Sold "
                    "UNITED STATES OIL FUND LP 91232N108 "
                    "1,000- 4.86 4,859.77 4,859.77"
                ),
                "1:8 R/S 4/29/20 91232N207",
                "Regulatory Fee 0.23",
            )
        )
    )

    assert len(events) == 2

    trade = events[0]
    fee = events[1]

    assert isinstance(trade, TradeEvent)
    assert isinstance(fee, FeeEvent)

    assert symbol_of(trade.security) == "USO"
    assert trade.side is TradeSide.SELL
    assert trade.quantity == Decimal("1000")
    assert trade.price == Decimal("4.86")
    assert trade.amount == Decimal("4859.77")

    raw_text = trade.evidence[0].raw_text

    assert raw_text is not None
    assert "91232N108" in raw_text
    assert "1:8 R/S 4/29/20 91232N207" in raw_text

    assert fee.amount == Decimal("0.23")


def test_parse_activity_resolves_uso_cusip_on_buy() -> None:
    """CUSIP resolution should work for purchases as well as sales."""
    events = parse_page(
        "\n".join(  # noqa: FLY002
            (
                "Account Activity",
                (
                    "04/22/20 04/24/20 Cash Buy - Securities Purchased "
                    "UNITED STATES OIL FUND LP 91232N108 "
                    "1,500 2.89 (4,335.00) (4,335.00)"
                ),
                "1:8 R/S 4/29/20 91232N207",
            )
        )
    )

    assert len(events) == 1

    trade = events[0]

    assert isinstance(trade, TradeEvent)
    assert symbol_of(trade.security) == "USO"
    assert trade.side is TradeSide.BUY
    assert trade.quantity == Decimal("1500")
    assert trade.price == Decimal("2.89")
    assert trade.amount == Decimal("4335.00")


def test_parse_activity_resolves_jnug_cusip() -> None:
    """JNUG reverse-split CUSIPs should resolve to the ticker."""
    events = parse_page(
        "\n".join(  # noqa: FLY002
            (
                "Account Activity",
                (
                    "04/06/20 04/08/20 Cash Sell - Securities Sold "
                    "DIREXION SHARES ETF TRUST 25460E166 "
                    "1,000- 5.10 5,099.77 5,099.77"
                ),
                "1:10 R/S 4/23/20 25460G831",
                "Regulatory Fee 0.23",
            )
        )
    )

    assert len(events) == 2

    trade = events[0]

    assert isinstance(trade, TradeEvent)
    assert symbol_of(trade.security) == "JNUG"
    assert trade.quantity == Decimal("1000")


def test_parse_activity_rejects_unknown_cusip() -> None:
    """Unknown security identifiers should fail explicitly."""
    row = (
        "04/02/20 04/06/20 Cash Sell - Securities Sold "
        "UNKNOWN SECURITY 12345A678 "
        "100- 10.00 1,000.00 1,000.00"
    )

    with pytest.raises(
        UnresolvedSecurityError,
        match="Unresolved security identifier",
    ):
        parse_page(
            f"Account Activity\n{row}",
        )
