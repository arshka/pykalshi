from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, ConfigDict
from .enums import OrderStatus, Side, Action, OrderType


class MarketModel(BaseModel):
    """Pydantic model for Market data."""

    ticker: str
    series_ticker: Optional[str] = None
    event_ticker: Optional[str] = None
    title: Optional[str] = None

    # Timing
    open_time: Optional[str] = None
    close_time: Optional[str] = None
    expiration_time: Optional[str] = None
    created_time: Optional[str] = None

    # Status & Result
    status: Optional[str] = None
    result: Optional[str] = None
    settlement_value: Optional[int] = None

    # Pricing
    yes_bid: Optional[int] = None
    yes_ask: Optional[int] = None
    no_bid: Optional[int] = None
    no_ask: Optional[int] = None
    last_price: Optional[int] = None

    # Volume & Liquidity
    volume: Optional[int] = None
    volume_24h: Optional[int] = None
    open_interest: Optional[int] = None
    liquidity: Optional[int] = None

    # Allow extra fields safely
    model_config = ConfigDict(extra="ignore")


class OrderModel(BaseModel):
    """Pydantic model for Order data."""

    order_id: str
    ticker: str
    status: OrderStatus
    action: Optional[Action] = None
    side: Optional[Side] = None
    count: Optional[int] = None
    yes_price: Optional[int] = None
    type: Optional[OrderType] = None

    model_config = ConfigDict(extra="ignore")


class BalanceModel(BaseModel):
    """Pydantic model for Balance data."""

    balance: int
    portfolio_value: int

    model_config = ConfigDict(extra="ignore")


class PositionModel(BaseModel):
    """Pydantic model for a portfolio position."""

    ticker: str
    event_ticker: Optional[str] = None
    event_exposure: Optional[int] = None
    position: int  # Net position (positive = yes contracts, negative = no contracts)
    total_traded: Optional[int] = None
    resting_orders_count: Optional[int] = None
    fees_paid: Optional[int] = None
    realized_pnl: Optional[int] = None

    model_config = ConfigDict(extra="ignore")


class FillModel(BaseModel):
    """Pydantic model for a trade fill/execution."""

    trade_id: str
    ticker: str
    order_id: str
    side: Side
    action: Action
    count: int
    yes_price: int
    no_price: int
    created_time: Optional[str] = None
    is_taker: Optional[bool] = None

    model_config = ConfigDict(extra="ignore")


class OHLCData(BaseModel):
    """OHLC price data."""

    open: Optional[int] = None
    high: Optional[int] = None
    low: Optional[int] = None
    close: Optional[int] = None
    open_dollars: Optional[str] = None
    high_dollars: Optional[str] = None
    low_dollars: Optional[str] = None
    close_dollars: Optional[str] = None

    model_config = ConfigDict(extra="ignore")


class PriceData(BaseModel):
    """Price data with additional fields."""

    open: Optional[int] = None
    high: Optional[int] = None
    low: Optional[int] = None
    close: Optional[int] = None
    max: Optional[int] = None
    min: Optional[int] = None
    mean: Optional[int] = None
    previous: Optional[int] = None

    model_config = ConfigDict(extra="ignore")


class Candlestick(BaseModel):
    """Pydantic model for a single Candlestick."""

    end_period_ts: int
    volume: int
    open_interest: int
    price: PriceData
    yes_bid: Optional[OHLCData] = None
    yes_ask: Optional[OHLCData] = None

    model_config = ConfigDict(extra="ignore")

    @property
    def timestamp_ms(self) -> int:
        """Timestamp in milliseconds (for consistency with Binance)."""
        return self.end_period_ts * 1000

    def to_bar(self) -> dict:
        """Convert to common bar format for unified backtesting.

        Returns:
            Dict with timestamp (ms), open, high, low, close, volume.
            Prices are in cents (1-99).
        """
        return {
            "timestamp": self.timestamp_ms,
            "open": float(self.price.open or 0),
            "high": float(self.price.high or 0),
            "low": float(self.price.low or 0),
            "close": float(self.price.close or 0),
            "volume": float(self.volume),
        }


class CandlestickResponse(BaseModel):
    """Pydantic model for Candlestick API response."""

    candlesticks: list[Candlestick]
    ticker: str

    model_config = ConfigDict(extra="ignore")
