from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .models import MarketModel, CandlestickResponse, OrderbookResponse, SeriesModel, TradeModel
from .dataframe import DataFrameList
from .enums import CandlestickPeriod, MarketStatus

if TYPE_CHECKING:
    from .client import KalshiClient
    from .events import Event, AsyncEvent

logger = logging.getLogger(__name__)


class Market:
    """Represents a Kalshi Market.

    Key fields are exposed as typed properties for IDE support.
    All other MarketModel fields are accessible via attribute delegation.
    """

    def __init__(self, client: KalshiClient, data: MarketModel) -> None:
        self._client = client
        self.data = data

    # --- Typed properties for core fields ---

    @property
    def ticker(self) -> str:
        return self.data.ticker

    @property
    def event_ticker(self) -> str | None:
        return self.data.event_ticker

    @property
    def status(self) -> MarketStatus | None:
        return self.data.status

    @property
    def title(self) -> str | None:
        return self.data.title

    @property
    def subtitle(self) -> str | None:
        return self.data.subtitle

    @property
    def yes_bid_dollars(self) -> str | None:
        return self.data.yes_bid_dollars

    @property
    def yes_ask_dollars(self) -> str | None:
        return self.data.yes_ask_dollars

    @property
    def no_bid_dollars(self) -> str | None:
        return self.data.no_bid_dollars

    @property
    def no_ask_dollars(self) -> str | None:
        return self.data.no_ask_dollars

    @property
    def last_price_dollars(self) -> str | None:
        return self.data.last_price_dollars

    @property
    def volume_fp(self) -> str | None:
        return self.data.volume_fp

    @property
    def volume_24h_fp(self) -> str | None:
        return self.data.volume_24h_fp

    @property
    def open_interest_fp(self) -> str | None:
        return self.data.open_interest_fp

    @property
    def liquidity_dollars(self) -> str | None:
        return self.data.liquidity_dollars

    @property
    def open_time(self) -> str | None:
        return self.data.open_time

    @property
    def close_time(self) -> str | None:
        return self.data.close_time

    @property
    def result(self) -> str | None:
        return self.data.result

    @property
    def series_ticker(self) -> str | None:
        return self.data.series_ticker

    def resolve_series_ticker(self) -> str | None:
        """Fetch series_ticker from the event API if not present in market data."""
        if self.data.series_ticker is not None:
            return self.data.series_ticker
        if not self.data.event_ticker:
            return None
        try:
            event_response = self._client.get(f"/events/{self.data.event_ticker}")
            return event_response["event"]["series_ticker"]
        except Exception as e:
            logger.warning(
                "Failed to resolve series_ticker for %s: %s", self.data.ticker, e
            )
            return None

    def get_orderbook(self, *, depth: int | None = None) -> OrderbookResponse:
        """Get the orderbook for this market."""
        endpoint = f"/markets/{self.data.ticker}/orderbook"
        if depth:
            endpoint += f"?depth={depth}"
        response = self._client.get(endpoint)
        return OrderbookResponse.model_validate(response)

    def get_candlesticks(
        self,
        start_ts: int,
        end_ts: int,
        period: CandlestickPeriod = CandlestickPeriod.ONE_HOUR,
    ) -> CandlestickResponse:
        """Get candlestick data for this market."""
        series = self.resolve_series_ticker()
        if not series:
            raise ValueError(f"Market {self.data.ticker} does not have a series_ticker.")

        query = f"start_ts={start_ts}&end_ts={end_ts}&period_interval={period.value}"
        endpoint = f"/series/{series}/markets/{self.data.ticker}/candlesticks?{query}"
        response = self._client.get(endpoint)
        return CandlestickResponse.model_validate(response)

    def get_trades(
        self,
        min_ts: int | None = None,
        max_ts: int | None = None,
        limit: int = 100,
        cursor: str | None = None,
        fetch_all: bool = False,
    ) -> DataFrameList[TradeModel]:
        """Get public trade history for this market."""
        return self._client.get_trades(
            ticker=self.ticker,
            min_ts=min_ts,
            max_ts=max_ts,
            limit=limit,
            cursor=cursor,
            fetch_all=fetch_all,
        )

    def get_event(self) -> Event | None:
        """Get the parent Event for this market."""
        if not self.event_ticker:
            return None
        return self._client.get_event(self.event_ticker)

    def __getattr__(self, name: str):
        return getattr(self.data, name)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Market):
            return NotImplemented
        return self.data.ticker == other.data.ticker

    def __hash__(self) -> int:
        return hash(self.data.ticker)

    def __repr__(self) -> str:
        status = self.status.value if self.status else "?"
        parts = [f"<Market {self.ticker}", status]

        if self.result:
            parts.append(self.result.upper())
        else:
            bid = self.yes_bid_dollars if self.yes_bid_dollars is not None else "?"
            ask = self.yes_ask_dollars if self.yes_ask_dollars is not None else "?"
            parts.append(f"${bid}/${ask}")
            if self.last_price_dollars is not None:
                parts.append(f"last=${self.last_price_dollars}")

        return " | ".join(parts) + ">"

    def _repr_html_(self) -> str:
        from ._repr import market_html
        return market_html(self)


class Series:
    """Represents a Kalshi Series (collection of related markets)."""

    def __init__(self, client: KalshiClient, data: SeriesModel) -> None:
        self._client = client
        self.data = data

    @property
    def ticker(self) -> str:
        return self.data.ticker

    @property
    def title(self) -> str | None:
        return self.data.title

    @property
    def category(self) -> str | None:
        return self.data.category

    def get_markets(self, **kwargs) -> DataFrameList[Market]:
        """Get all markets in this series."""
        return self._client.get_markets(series_ticker=self.ticker, **kwargs)

    def get_events(self, **kwargs) -> DataFrameList[Event]:
        """Get all events in this series."""
        return self._client.get_events(series_ticker=self.ticker, **kwargs)

    def __getattr__(self, name: str):
        return getattr(self.data, name)

    def __repr__(self) -> str:
        parts = [f"<Series {self.ticker}"]
        if self.category:
            parts.append(self.category)
        if self.title:
            parts.append(self.title)
        return " | ".join(parts) + ">"

    def _repr_html_(self) -> str:
        from ._repr import series_html
        return series_html(self)


class AsyncMarket(Market):
    """Async variant of Market. Inherits all properties and non-I/O methods."""

    async def resolve_series_ticker(self) -> str | None:  # type: ignore[override]
        if self.data.series_ticker is not None:
            return self.data.series_ticker
        if not self.data.event_ticker:
            return None
        try:
            event_response = await self._client.get(f"/events/{self.data.event_ticker}")
            return event_response["event"]["series_ticker"]
        except Exception as e:
            logger.warning("Failed to resolve series_ticker for %s: %s", self.data.ticker, e)
            return None

    async def get_orderbook(self, *, depth: int | None = None) -> OrderbookResponse:  # type: ignore[override]
        endpoint = f"/markets/{self.data.ticker}/orderbook"
        if depth:
            endpoint += f"?depth={depth}"
        response = await self._client.get(endpoint)
        return OrderbookResponse.model_validate(response)

    async def get_candlesticks(  # type: ignore[override]
        self, start_ts: int, end_ts: int,
        period: CandlestickPeriod = CandlestickPeriod.ONE_HOUR,
    ) -> CandlestickResponse:
        series = await self.resolve_series_ticker()
        if not series:
            raise ValueError(f"Market {self.data.ticker} does not have a series_ticker.")
        query = f"start_ts={start_ts}&end_ts={end_ts}&period_interval={period.value}"
        endpoint = f"/series/{series}/markets/{self.data.ticker}/candlesticks?{query}"
        response = await self._client.get(endpoint)
        return CandlestickResponse.model_validate(response)

    async def get_trades(  # type: ignore[override]
        self, min_ts=None, max_ts=None, limit=100, cursor=None, fetch_all=False,
    ) -> DataFrameList[TradeModel]:
        return await self._client.get_trades(
            ticker=self.ticker, min_ts=min_ts, max_ts=max_ts,
            limit=limit, cursor=cursor, fetch_all=fetch_all,
        )

    async def get_event(self) -> AsyncEvent | None:  # type: ignore[override]
        if not self.event_ticker:
            return None
        return await self._client.get_event(self.event_ticker)


class AsyncSeries(Series):
    """Async variant of Series. Inherits all properties and non-I/O methods."""

    async def get_markets(self, **kwargs) -> DataFrameList[AsyncMarket]:  # type: ignore[override]
        return await self._client.get_markets(series_ticker=self.ticker, **kwargs)

    async def get_events(self, **kwargs) -> DataFrameList[AsyncEvent]:  # type: ignore[override]
        return await self._client.get_events(series_ticker=self.ticker, **kwargs)
