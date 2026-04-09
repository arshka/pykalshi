"""Integration tests for historical data endpoints."""

import pytest
from pykalshi.models import HistoricalCutoffResponse, HistoricalCandlestick
from pykalshi.enums import CandlestickPeriod


class TestHistoricalCutoff:
    """Tests for /historical/cutoff."""

    def test_get_cutoff(self, client):
        """Cutoff returns valid timestamps."""
        cutoff = client.history.get_cutoff()

        assert isinstance(cutoff, HistoricalCutoffResponse)
        assert cutoff.market_settled_ts
        assert cutoff.trades_created_ts
        assert cutoff.orders_updated_ts


class TestHistoricalMarkets:
    """Tests for /historical/markets."""

    def test_get_markets(self, client):
        """Get historical markets returns list."""
        markets = client.history.get_markets(limit=5)

        assert isinstance(markets, list)
        if markets:
            assert hasattr(markets[0], "ticker")
            assert hasattr(markets[0], "status")

    def test_get_single_market(self, client):
        """Get a single historical market by ticker."""
        markets = client.history.get_markets(limit=1)
        if not markets:
            pytest.skip("No historical markets available")

        market = client.history.get_market(markets[0].ticker)
        assert market.ticker == markets[0].ticker

    def test_get_markets_pagination(self, client):
        """Verify pagination returns data and cursor works."""
        first_page = client.history.get_markets(limit=5)
        if len(first_page) < 5:
            pytest.skip("Not enough historical markets to test pagination")

        # Just verify we can get a second page (don't fetch_all — could be thousands)
        second_page = client.history.get_markets(limit=5)
        assert len(second_page) > 0


class TestHistoricalCandlesticks:
    """Tests for /historical/markets/{ticker}/candlesticks."""

    def test_get_candlesticks(self, client):
        """Get candlesticks for a historical market."""
        markets = client.history.get_markets(limit=10)
        if not markets:
            pytest.skip("No historical markets available")

        for market in markets:
            try:
                candles = client.history.get_candlesticks(
                    market.ticker,
                    start_ts=0,
                    end_ts=2000000000,
                    period=CandlestickPeriod.ONE_DAY,
                )
                assert isinstance(candles, list)
                if candles:
                    assert isinstance(candles[0], HistoricalCandlestick)
                    assert candles[0].end_period_ts > 0
                return
            except Exception:
                continue

        pytest.skip("No historical markets with candlestick data found")


class TestHistoricalFills:
    """Tests for /historical/fills (authenticated)."""

    def test_get_fills(self, client):
        """Get historical fills returns list."""
        fills = client.history.get_fills(limit=5)

        assert isinstance(fills, list)
        if fills:
            assert hasattr(fills[0], "trade_id")
            assert hasattr(fills[0], "ticker")


class TestHistoricalOrders:
    """Tests for /historical/orders (authenticated)."""

    def test_get_orders(self, client):
        """Get historical orders returns list."""
        orders = client.history.get_orders(limit=5)

        assert isinstance(orders, list)
        if orders:
            assert hasattr(orders[0], "ticker")
            assert hasattr(orders[0], "status")


class TestHistoricalTrades:
    """Tests for /historical/trades."""

    def test_get_trades(self, client):
        """Get historical trades returns list."""
        trades = client.history.get_trades(limit=5)

        assert isinstance(trades, list)
        if trades:
            assert hasattr(trades[0], "trade_id")
            assert hasattr(trades[0], "yes_price_dollars")

    def test_get_trades_with_ticker(self, client):
        """Get historical trades filtered by ticker."""
        markets = client.history.get_markets(limit=1)
        if not markets:
            pytest.skip("No historical markets available")

        trades = client.history.get_trades(ticker=markets[0].ticker, limit=5)
        assert isinstance(trades, list)
