"""Tests for Market and Event functionality."""

import pytest
from unittest.mock import ANY

from kalshi_api import Market, Event
from kalshi_api.enums import MarketStatus, CandlestickPeriod


class TestGetMarket:
    """Tests for fetching single markets."""

    def test_get_market(self, client, mock_response):
        """Test fetching a market by ticker."""
        client._session.request.return_value = mock_response({
            "market": {
                "ticker": "KXTEST-A",
                "event_ticker": "KXTEST",
                "title": "Test Market",
                "status": "open",
                "yes_bid": 45,
                "yes_ask": 55,
                "volume": 1000,
            }
        })

        market = client.get_market("KXTEST-A")

        assert isinstance(market, Market)
        assert market.ticker == "KXTEST-A"
        assert market.title == "Test Market"
        assert market.yes_bid == 45
        assert market.yes_ask == 55

    def test_get_market_not_found(self, client, mock_response):
        """Test fetching non-existent market raises error."""
        from kalshi_api.exceptions import ResourceNotFoundError

        client._session.request.return_value = mock_response(
            {"message": "Market not found"}, status_code=404
        )

        with pytest.raises(ResourceNotFoundError):
            client.get_market("NONEXISTENT")


class TestGetMarkets:
    """Tests for listing markets."""

    def test_get_markets(self, client, mock_response):
        """Test listing markets."""
        client._session.request.return_value = mock_response({
            "markets": [
                {"ticker": "KXTEST-A", "status": "open"},
                {"ticker": "KXTEST-B", "status": "open"},
            ],
            "cursor": "",
        })

        markets = client.get_markets()

        assert len(markets) == 2
        assert all(isinstance(m, Market) for m in markets)

    def test_get_markets_with_filters(self, client, mock_response):
        """Test listing markets with filters."""
        client._session.request.return_value = mock_response({
            "markets": [],
            "cursor": "",
        })

        client.get_markets(
            series_ticker="INXD",
            event_ticker="KXTEST",
            status=MarketStatus.OPEN,
            limit=50,
        )

        call_url = client._session.request.call_args.args[1]
        assert "series_ticker=INXD" in call_url
        assert "event_ticker=KXTEST" in call_url
        assert "status=open" in call_url
        assert "limit=50" in call_url

    def test_get_markets_pagination(self, client, mock_response):
        """Test markets pagination with fetch_all."""
        client._session.request.side_effect = [
            mock_response({
                "markets": [{"ticker": "M1"}],
                "cursor": "page2",
            }),
            mock_response({
                "markets": [{"ticker": "M2"}],
                "cursor": "",
            }),
        ]

        markets = client.get_markets(fetch_all=True)

        assert len(markets) == 2
        assert client._session.request.call_count == 2


class TestMarketCandlesticks:
    """Tests for market candlestick data."""

    def test_get_candlesticks(self, client, mock_response):
        """Test fetching candlesticks for a market."""
        client._session.request.side_effect = [
            # First call: get market
            mock_response({
                "market": {
                    "ticker": "INXD-24JAN01",
                    "series_ticker": "INXD",
                }
            }),
            # Second call: get candlesticks
            mock_response({
                "ticker": "INXD-24JAN01",
                "candlesticks": [
                    {
                        "end_period_ts": 1704067200,
                        "volume": 100,
                        "open_interest": 500,
                        "price": {"open": 50, "high": 55, "low": 48, "close": 53},
                    },
                    {
                        "end_period_ts": 1704070800,
                        "volume": 150,
                        "open_interest": 520,
                        "price": {"open": 53, "high": 58, "low": 52, "close": 56},
                    },
                ],
            }),
        ]

        market = client.get_market("INXD-24JAN01")
        candles = market.get_candlesticks(
            start_ts=1704000000,
            end_ts=1704100000,
            period=CandlestickPeriod.ONE_HOUR,
        )

        assert candles.ticker == "INXD-24JAN01"
        assert len(candles.candlesticks) == 2
        assert candles.candlesticks[0].volume == 100
        assert candles.candlesticks[0].price.open == 50

    def test_get_candlesticks_no_series_ticker_error(self, client, mock_response):
        """Test candlesticks raises error when series_ticker missing."""
        client._session.request.return_value = mock_response({
            "market": {
                "ticker": "ORPHAN",
                "series_ticker": None,
                "event_ticker": None,
            }
        })

        market = client.get_market("ORPHAN")

        with pytest.raises(ValueError, match="series_ticker"):
            market.get_candlesticks(start_ts=1, end_ts=2)

    def test_get_candlesticks_resolves_series_from_event(self, client, mock_response):
        """Test candlesticks resolves series_ticker from event if missing."""
        client._session.request.side_effect = [
            # First call: get market (no series_ticker)
            mock_response({
                "market": {
                    "ticker": "KXTEST-A",
                    "series_ticker": None,
                    "event_ticker": "KXTEST",
                }
            }),
            # Second call: resolve series from event
            mock_response({
                "event": {
                    "event_ticker": "KXTEST",
                    "series_ticker": "KXSERIES",
                }
            }),
            # Third call: get candlesticks
            mock_response({
                "ticker": "KXTEST-A",
                "candlesticks": [],
            }),
        ]

        market = client.get_market("KXTEST-A")
        candles = market.get_candlesticks(start_ts=1, end_ts=2)

        assert candles.ticker == "KXTEST-A"
        # Verify series was resolved
        assert market.series_ticker == "KXSERIES"


class TestMarketObject:
    """Tests for Market object methods and properties."""

    def test_market_equality(self, client, mock_response):
        """Test Market equality is based on ticker."""
        client._session.request.side_effect = [
            mock_response({"market": {"ticker": "TEST"}}),
            mock_response({"market": {"ticker": "TEST"}}),
            mock_response({"market": {"ticker": "OTHER"}}),
        ]

        m1 = client.get_market("TEST")
        m2 = client.get_market("TEST")
        m3 = client.get_market("OTHER")

        assert m1 == m2
        assert m1 != m3
        assert hash(m1) == hash(m2)

    def test_market_repr(self, client, mock_response):
        """Test Market string representation."""
        client._session.request.return_value = mock_response({
            "market": {"ticker": "KXTEST"}
        })

        market = client.get_market("KXTEST")

        assert repr(market) == "<Market KXTEST>"

    def test_market_attribute_delegation(self, client, mock_response):
        """Test Market delegates unknown attributes to data."""
        client._session.request.return_value = mock_response({
            "market": {
                "ticker": "TEST",
                "rules_primary": "Test rules here",
                "tick_size": 1,
            }
        })

        market = client.get_market("TEST")

        assert market.rules_primary == "Test rules here"
        assert market.tick_size == 1


class TestGetEvent:
    """Tests for fetching events."""

    def test_get_event(self, client, mock_response):
        """Test fetching an event by ticker."""
        client._session.request.return_value = mock_response({
            "event": {
                "event_ticker": "KXTEST",
                "series_ticker": "KXSERIES",
                "title": "Test Event",
                "category": "politics",
            }
        })

        event = client.get_event("KXTEST")

        assert isinstance(event, Event)
        assert event.event_ticker == "KXTEST"
        assert event.series_ticker == "KXSERIES"
        assert event.title == "Test Event"

    def test_get_event_not_found(self, client, mock_response):
        """Test fetching non-existent event raises error."""
        from kalshi_api.exceptions import ResourceNotFoundError

        client._session.request.return_value = mock_response(
            {"message": "Event not found"}, status_code=404
        )

        with pytest.raises(ResourceNotFoundError):
            client.get_event("NONEXISTENT")


class TestGetEvents:
    """Tests for listing events."""

    def test_get_events(self, client, mock_response):
        """Test listing events."""
        client._session.request.return_value = mock_response({
            "events": [
                {"event_ticker": "E1", "series_ticker": "S1", "title": "Event 1"},
                {"event_ticker": "E2", "series_ticker": "S1", "title": "Event 2"},
            ],
            "cursor": "",
        })

        events = client.get_events()

        assert len(events) == 2
        assert all(isinstance(e, Event) for e in events)

    def test_get_events_with_filters(self, client, mock_response):
        """Test listing events with filters."""
        client._session.request.return_value = mock_response({
            "events": [],
            "cursor": "",
        })

        client.get_events(
            series_ticker="KXSERIES",
            status=MarketStatus.OPEN,
            limit=25,
        )

        call_url = client._session.request.call_args.args[1]
        assert "series_ticker=KXSERIES" in call_url
        assert "status=open" in call_url
        assert "limit=25" in call_url

    def test_get_events_pagination(self, client, mock_response):
        """Test events pagination with fetch_all."""
        client._session.request.side_effect = [
            mock_response({
                "events": [{"event_ticker": "E1", "series_ticker": "S"}],
                "cursor": "page2",
            }),
            mock_response({
                "events": [{"event_ticker": "E2", "series_ticker": "S"}],
                "cursor": "",
            }),
        ]

        events = client.get_events(fetch_all=True)

        assert len(events) == 2
        assert client._session.request.call_count == 2


class TestMarketStatus:
    """Tests for MarketStatus enum usage."""

    def test_market_status_values(self):
        """Test MarketStatus enum has expected values."""
        assert MarketStatus.OPEN.value == "open"
        assert MarketStatus.CLOSED.value == "closed"
        assert MarketStatus.SETTLED.value == "settled"

    def test_market_with_status(self, client, mock_response):
        """Test market status is properly parsed."""
        client._session.request.return_value = mock_response({
            "market": {"ticker": "TEST", "status": "open"}
        })

        market = client.get_market("TEST")

        assert market.status == MarketStatus.OPEN
