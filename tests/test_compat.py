"""Tests for backward-compatibility layer (_compat.py)."""

import json
import warnings
import pytest
from unittest.mock import ANY

from pykalshi._compat import (
    dollars_to_cents, fp_to_int, cents_to_dollars, int_to_fp,
    orderbook_to_legacy, CompatModel, convert_legacy_kwargs,
    PLACE_ORDER_LEGACY, AMEND_ORDER_LEGACY, DECREASE_ORDER_LEGACY,
    BATCH_ORDER_LEGACY, ORDER_GROUP_LEGACY, TRANSFER_LEGACY, RFQ_LEGACY,
)
from pykalshi.models import (
    MarketModel, OrderModel, BalanceModel, PositionModel,
    FillModel, TradeModel, SettlementModel, OrderGroupModel,
    Orderbook, OHLCData, PriceData, Candlestick,
    SubaccountBalanceModel, SubaccountTransferModel,
    ForecastPoint, RfqModel, QuoteModel,
)
from pykalshi.feed import (
    TickerMessage, OrderbookSnapshotMessage, OrderbookDeltaMessage,
    TradeMessage, FillMessage, PositionMessage,
)
from pykalshi.enums import Action, Side, OrderType, OrderStatus
from pykalshi.portfolio import Portfolio


# --- Conversion function tests ---

class TestConversionFunctions:
    def test_dollars_to_cents(self):
        assert dollars_to_cents("0.45") == 45
        assert dollars_to_cents("1.00") == 100
        assert dollars_to_cents("0.999") == 99  # truncates
        assert dollars_to_cents(None) is None

    def test_fp_to_int(self):
        assert fp_to_int("100.50") == 100  # truncates
        assert fp_to_int("5") == 5
        assert fp_to_int(None) is None

    def test_cents_to_dollars(self):
        assert cents_to_dollars(45) == "0.45"
        assert cents_to_dollars(100) == "1.00"
        assert cents_to_dollars(50) == "0.50"
        assert cents_to_dollars(0) == "0.00"

    def test_int_to_fp(self):
        assert int_to_fp(5) == "5.00"
        assert int_to_fp(100) == "100.00"
        assert int_to_fp(0) == "0.00"

    def test_orderbook_to_legacy(self):
        levels = [("0.45", "10.00"), ("0.50", "20.50")]
        result = orderbook_to_legacy(levels)
        assert result == [(45, 10), (50, 20)]
        assert orderbook_to_legacy(None) is None


# --- CompatModel legacy accessor tests ---

class TestMarketModelLegacy:
    def test_yes_bid_legacy(self):
        m = MarketModel(ticker="TEST", yes_bid_dollars="0.45")
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            val = m.yes_bid
            assert val == 45
            assert len(w) == 1
            assert "yes_bid" in str(w[0].message)
            assert issubclass(w[0].category, DeprecationWarning)

    def test_volume_legacy(self):
        m = MarketModel(ticker="TEST", volume_fp="1000.50")
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            val = m.volume
            assert val == 1000
            assert len(w) == 1

    def test_none_propagation(self):
        m = MarketModel(ticker="TEST")
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            assert m.yes_bid is None
            assert len(w) == 1

    def test_new_field_still_works(self):
        m = MarketModel(ticker="TEST", yes_bid_dollars="0.45")
        assert m.yes_bid_dollars == "0.45"

    def test_nonexistent_attr_raises(self):
        m = MarketModel(ticker="TEST")
        with pytest.raises(AttributeError):
            m.nonexistent_field


class TestOrderModelLegacy:
    def test_yes_price_legacy(self):
        m = OrderModel(order_id="123", ticker="TEST", status="resting",
                       yes_price_dollars="0.50")
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            assert m.yes_price == 50
            assert len(w) == 1

    def test_initial_count_legacy(self):
        m = OrderModel(order_id="123", ticker="TEST", status="resting",
                       initial_count_fp="10.00")
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            assert m.initial_count == 10
            assert len(w) == 1


class TestBalanceModelLegacy:
    def test_balance_dollars_legacy(self):
        m = BalanceModel(balance=5000, portfolio_value=10000)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            val = m.balance_dollars
            assert val == "50.00"
            assert len(w) == 1
            assert "balance_dollars" in str(w[0].message)
            assert issubclass(w[0].category, DeprecationWarning)


class TestPositionModelLegacy:
    def test_position_legacy(self):
        m = PositionModel(ticker="TEST", position_fp="10.50")
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            assert m.position == 10
            assert len(w) == 1

    def test_market_exposure_legacy(self):
        m = PositionModel(ticker="TEST", position_fp="0", market_exposure_dollars="5.00")
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            assert m.market_exposure == 500
            assert len(w) == 1


class TestOrderbookLegacy:
    def test_yes_no_legacy(self):
        ob = Orderbook(yes_dollars=[("0.45", "10.00")], no_dollars=[("0.55", "20.00")])
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            assert ob.yes == [(45, 10)]
            assert ob.no == [(55, 20)]
            assert len(w) == 2


class TestSettlementModelLegacy:
    def test_revenue_dollars_legacy(self):
        m = SettlementModel(ticker="TEST", revenue=1000)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            val = m.revenue_dollars
            assert val == "10.00"
            assert len(w) == 1
            assert "revenue_dollars" in str(w[0].message)
            assert issubclass(w[0].category, DeprecationWarning)


class TestFillModelLegacy:
    def test_count_legacy(self):
        m = FillModel(trade_id="t1", ticker="TEST", order_id="o1",
                      side="yes", action="buy", count_fp="5.00",
                      yes_price_fixed="0.50", no_price_fixed="0.50")
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            assert m.count == 5
            assert len(w) == 1

    def test_yes_price_dollars_legacy(self):
        m = FillModel(trade_id="t1", ticker="TEST", order_id="o1",
                      side="yes", action="buy", count_fp="5.00",
                      yes_price_fixed="0.50", no_price_fixed="0.50")
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            assert m.yes_price_dollars == "0.50"
            assert len(w) == 1


# --- Feed model legacy accessor tests ---

class TestFeedModelLegacy:
    def test_ticker_message(self):
        msg = TickerMessage(market_ticker="TEST", price_dollars="0.45",
                            volume_fp="1000")
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            assert msg.price == 45
            assert msg.volume == 1000
            assert len(w) == 2

    def test_orderbook_snapshot(self):
        msg = OrderbookSnapshotMessage(
            market_ticker="TEST",
            yes_dollars=[("0.45", "10.00")],
            no_dollars=[("0.55", "20.00")],
        )
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            assert msg.yes == [(45, 10)]
            assert msg.no == [(55, 20)]
            assert len(w) == 2

    def test_orderbook_delta(self):
        msg = OrderbookDeltaMessage(
            market_ticker="TEST", price_dollars="0.45", delta_fp="5", side="yes"
        )
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            assert msg.price == 45
            assert msg.delta == 5
            assert len(w) == 2

    def test_trade_message(self):
        msg = TradeMessage(market_ticker="TEST", yes_price_dollars="0.50",
                           count_fp="10")
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            assert msg.yes_price == 50
            assert msg.count == 10
            assert len(w) == 2

    def test_fill_message(self):
        msg = FillMessage(yes_price_dollars="0.50", no_price_dollars="0.50",
                          count_fp="5")
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            assert msg.yes_price == 50
            assert msg.count == 5
            assert len(w) == 2

    def test_position_message(self):
        msg = PositionMessage(ticker="TEST", position_fp="10.50",
                              market_exposure_dollars="5.00")
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            assert msg.position == 10
            assert msg.market_exposure == 500
            assert len(w) == 2


# --- POST param conversion tests ---

class TestConvertLegacyKwargs:
    def test_basic_conversion(self):
        kw = {"yes_price": 45, "count": 5}
        convert_legacy_kwargs(kw, PLACE_ORDER_LEGACY)
        assert kw == {"yes_price_dollars": "0.45", "count_fp": "5.00"}

    def test_new_param_takes_precedence(self):
        kw = {"yes_price": 45, "yes_price_dollars": "0.50"}
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            convert_legacy_kwargs(kw, PLACE_ORDER_LEGACY)
            assert kw["yes_price_dollars"] == "0.50"
            assert len(w) == 0  # no warning when new param present

    def test_none_old_param_ignored(self):
        kw = {"yes_price": None}
        convert_legacy_kwargs(kw, PLACE_ORDER_LEGACY)
        assert "yes_price_dollars" not in kw


class TestPlaceOrderLegacyParams:
    def test_legacy_count_and_price(self, client, mock_response):
        client._session.request.return_value = mock_response(
            {"order": {"order_id": "123", "ticker": "TEST", "status": "resting",
                        "action": "buy", "side": "yes", "initial_count_fp": "5.00",
                        "yes_price_dollars": "0.45"}}
        )

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            order = client.portfolio.place_order(
                "TEST", Action.BUY, Side.YES,
                count=5, yes_price=45,
            )

        # Verify correct payload sent
        call_args = client._session.request.call_args
        body = json.loads(call_args.kwargs["content"])
        assert body["count_fp"] == "5.00"
        assert body["yes_price_dollars"] == "0.45"

        # Verify deprecation warnings fired
        dep_warnings = [w_ for w_ in w if issubclass(w_.category, DeprecationWarning)]
        assert len(dep_warnings) == 2

    def test_legacy_no_price(self, client, mock_response):
        client._session.request.return_value = mock_response(
            {"order": {"order_id": "123", "ticker": "TEST", "status": "resting",
                        "action": "buy", "side": "no", "initial_count_fp": "5.00",
                        "no_price_dollars": "0.45"}}
        )

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            order = client.portfolio.place_order(
                "TEST", Action.BUY, Side.NO,
                count=5, no_price=45,
            )

        call_args = client._session.request.call_args
        body = json.loads(call_args.kwargs["content"])
        assert body["count_fp"] == "5.00"
        # no_price=45 → no_price_dollars="0.45" → converted to yes_price_dollars internally
        assert "yes_price_dollars" in body


class TestAmendOrderLegacyParams:
    def test_legacy_amend(self, client, mock_response):
        client._session.request.return_value = mock_response(
            {"order": {"order_id": "123", "ticker": "TEST", "status": "resting",
                        "action": "buy", "side": "yes", "initial_count_fp": "10.00",
                        "remaining_count_fp": "10.00", "yes_price_dollars": "0.50"}}
        )

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            client.portfolio.amend_order(
                "123", count=10, yes_price=50,
                ticker="TEST", action=Action.BUY, side=Side.YES,
            )

        call_args = client._session.request.call_args
        body = json.loads(call_args.kwargs["content"])
        assert body["count_fp"] == "10.00"
        assert body["yes_price_dollars"] == "0.50"


class TestDecreaseOrderLegacyParams:
    def test_legacy_reduce_by(self, client, mock_response):
        client._session.request.return_value = mock_response(
            {"order": {"order_id": "123", "ticker": "TEST", "status": "resting"}}
        )

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            client.portfolio.decrease_order("123", reduce_by=3)

        call_args = client._session.request.call_args
        body = json.loads(call_args.kwargs["content"])
        assert body["reduce_by_fp"] == "3.00"


class TestBatchOrdersLegacyParams:
    def test_legacy_batch_keys(self):
        orders = [
            {"ticker": "TEST", "action": "buy", "side": "yes",
             "count": 5, "yes_price": 45, "type": "limit"},
        ]
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            prepared = Portfolio._build_batch_orders(orders)

        assert prepared[0]["count_fp"] == "5.00"
        assert prepared[0]["yes_price_dollars"] == "0.45"
        assert "count" not in prepared[0]
        assert "yes_price" not in prepared[0]
        assert "type" not in prepared[0]  # "type" is stripped before sending to API


class TestOrderGroupLegacyParams:
    def test_legacy_create(self, client, mock_response):
        client._session.request.return_value = mock_response(
            {"id": "og-1", "contracts_limit_fp": "100"}
        )

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            client.portfolio.create_order_group(contracts_limit=100)

        call_args = client._session.request.call_args
        body = json.loads(call_args.kwargs["content"])
        assert body["contracts_limit_fp"] == "100.00"


class TestTransferLegacyParams:
    def test_legacy_amount(self, client, mock_response):
        client._session.request.return_value = mock_response(
            {"transfer": {"transfer_id": "t1", "from_subaccount_id": "sub1",
                          "to_subaccount_id": "sub2", "amount_dollars": "5.00"}}
        )

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            client.portfolio.transfer_between_subaccounts(
                "sub1", "sub2", amount=500,
            )

        call_args = client._session.request.call_args
        body = json.loads(call_args.kwargs["content"])
        assert body["amount_dollars"] == "5.00"
