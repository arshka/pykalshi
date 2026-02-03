from __future__ import annotations
from functools import cached_property
from typing import Optional
from pydantic import BaseModel, ConfigDict
from .enums import OrderStatus, Side, Action, OrderType, MarketStatus


class MarketModel(BaseModel):
    """Pydantic model for Market data."""

    ticker: str
    event_ticker: Optional[str] = None
    series_ticker: Optional[str] = None
    market_type: Optional[str] = None
    title: Optional[str] = None
    subtitle: Optional[str] = None
    yes_sub_title: Optional[str] = None
    no_sub_title: Optional[str] = None

    # Timing
    open_time: Optional[str] = None
    close_time: Optional[str] = None
    expiration_time: Optional[str] = None
    expected_expiration_time: Optional[str] = None
    latest_expiration_time: Optional[str] = None
    created_time: Optional[str] = None
    updated_time: Optional[str] = None

    # Status & Result
    status: Optional[MarketStatus] = None
    result: Optional[str] = None
    settlement_value: Optional[int] = None

    # Pricing
    yes_bid: Optional[int] = None
    yes_ask: Optional[int] = None
    no_bid: Optional[int] = None
    no_ask: Optional[int] = None
    last_price: Optional[int] = None
    previous_yes_bid: Optional[int] = None
    previous_yes_ask: Optional[int] = None
    previous_price: Optional[int] = None
    notional_value: Optional[int] = None

    # Volume & Liquidity
    volume: Optional[int] = None
    volume_24h: Optional[int] = None
    open_interest: Optional[int] = None
    liquidity: Optional[int] = None

    # Market structure
    tick_size: Optional[int] = None
    strike_type: Optional[str] = None
    can_close_early: Optional[bool] = None
    rules_primary: Optional[str] = None
    rules_secondary: Optional[str] = None

    model_config = ConfigDict(extra="ignore")


class EventModel(BaseModel):
    """Pydantic model for Event data."""

    event_ticker: str
    series_ticker: str
    title: Optional[str] = None
    sub_title: Optional[str] = None
    category: Optional[str] = None

    # Event properties
    mutually_exclusive: bool = False
    collateral_return_type: Optional[str] = None

    # Timing
    strike_date: Optional[str] = None
    strike_period: Optional[str] = None

    # Availability
    available_on_brokers: bool = False

    model_config = ConfigDict(extra="ignore")


class OrderModel(BaseModel):
    """Pydantic model for Order data."""

    order_id: str
    ticker: str
    status: OrderStatus
    action: Optional[Action] = None
    side: Optional[Side] = None
    type: Optional[OrderType] = None

    # Pricing
    yes_price: Optional[int] = None
    no_price: Optional[int] = None

    # Counts
    initial_count: Optional[int] = None
    fill_count: Optional[int] = None
    remaining_count: Optional[int] = None

    # Fees & costs (in cents)
    taker_fees: Optional[int] = None
    maker_fees: Optional[int] = None
    taker_fill_cost: Optional[int] = None
    maker_fill_cost: Optional[int] = None

    # Metadata
    user_id: Optional[str] = None
    client_order_id: Optional[str] = None
    created_time: Optional[str] = None
    last_update_time: Optional[str] = None
    expiration_time: Optional[str] = None

    model_config = ConfigDict(extra="ignore")


class BalanceModel(BaseModel):
    """Pydantic model for Balance data. Values are in cents."""

    balance: int
    portfolio_value: int
    updated_ts: Optional[int] = None

    model_config = ConfigDict(extra="ignore")


class PositionModel(BaseModel):
    """Pydantic model for a portfolio position."""

    ticker: str
    position: int  # Net position (positive = yes, negative = no)
    market_exposure: Optional[int] = None
    total_traded: Optional[int] = None
    resting_orders_count: Optional[int] = None
    fees_paid: Optional[int] = None
    realized_pnl: Optional[int] = None
    last_updated_ts: Optional[str] = None

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
    is_taker: Optional[bool] = None
    fill_id: Optional[str] = None
    market_ticker: Optional[str] = None
    fee_cost: Optional[str] = None  # Dollar amount string (e.g., "0.3200")
    created_time: Optional[str] = None
    ts: Optional[int] = None

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


class CandlestickResponse(BaseModel):
    """Pydantic model for Candlestick API response."""

    candlesticks: list[Candlestick]
    ticker: str

    model_config = ConfigDict(extra="ignore")


# Orderbook Models
class OrderbookLevel(BaseModel):
    """A single price level in the orderbook (price, quantity)."""

    price: int  # Price in cents (1-99)
    quantity: int  # Number of contracts at this price level

    model_config = ConfigDict(extra="ignore")


class Orderbook(BaseModel):
    """Orderbook with yes/no price levels."""

    yes: Optional[list[tuple[int, int]]] = None  # [(price, quantity), ...]
    no: Optional[list[tuple[int, int]]] = None
    yes_dollars: Optional[list[tuple[str, int]]] = None  # [(price_str, quantity_int), ...]
    no_dollars: Optional[list[tuple[str, int]]] = None

    model_config = ConfigDict(extra="ignore")


class OrderbookFp(BaseModel):
    """Fixed-point orderbook data."""

    yes_dollars: Optional[list[tuple[str, int]]] = None  # [(price_str, quantity_int), ...]
    no_dollars: Optional[list[tuple[str, int]]] = None

    model_config = ConfigDict(extra="ignore")


class OrderbookResponse(BaseModel):
    """Pydantic model for the orderbook API response."""

    orderbook: Orderbook
    orderbook_fp: Optional[OrderbookFp] = None

    model_config = ConfigDict(extra="ignore")

    @cached_property
    def yes_levels(self) -> list[OrderbookLevel]:
        """Get YES price levels as typed objects."""
        if not self.orderbook.yes:
            return []
        return [OrderbookLevel(price=p[0], quantity=p[1]) for p in self.orderbook.yes]

    @cached_property
    def no_levels(self) -> list[OrderbookLevel]:
        """Get NO price levels as typed objects."""
        if not self.orderbook.no:
            return []
        return [OrderbookLevel(price=p[0], quantity=p[1]) for p in self.orderbook.no]

    @cached_property
    def best_yes_bid(self) -> Optional[int]:
        """Highest YES bid price, or None if no bids."""
        if not self.orderbook.yes:
            return None
        return max(p[0] for p in self.orderbook.yes)

    @cached_property
    def best_no_bid(self) -> Optional[int]:
        """Highest NO bid price, or None if no bids."""
        if not self.orderbook.no:
            return None
        return max(p[0] for p in self.orderbook.no)

    @cached_property
    def best_yes_ask(self) -> Optional[int]:
        """Lowest YES ask (= 100 - best NO bid)."""
        if self.best_no_bid is None:
            return None
        return 100 - self.best_no_bid

    @cached_property
    def spread(self) -> Optional[int]:
        """Bid-ask spread in cents. None if no two-sided market."""
        if self.best_yes_bid is None or self.best_yes_ask is None:
            return None
        return self.best_yes_ask - self.best_yes_bid

    @cached_property
    def mid(self) -> Optional[float]:
        """Mid price. None if no two-sided market."""
        if self.best_yes_bid is None or self.best_yes_ask is None:
            return None
        return (self.best_yes_bid + self.best_yes_ask) / 2

    @cached_property
    def spread_bps(self) -> Optional[float]:
        """Spread as basis points of mid. None if no two-sided market."""
        if self.spread is None or self.mid is None or self.mid == 0:
            return None
        return (self.spread / self.mid) * 10000

    def yes_depth(self, through_price: int) -> int:
        """Total YES bid quantity at or above `through_price`."""
        if not self.orderbook.yes:
            return 0
        return sum(q for p, q in self.orderbook.yes if p >= through_price)

    def no_depth(self, through_price: int) -> int:
        """Total NO bid quantity at or above `through_price`."""
        if not self.orderbook.no:
            return 0
        return sum(q for p, q in self.orderbook.no if p >= through_price)

    @cached_property
    def imbalance(self) -> Optional[float]:
        """Order imbalance: (yes_depth - no_depth) / (yes_depth + no_depth). Range [-1, 1]."""
        yes_total = sum(q for _, q in self.orderbook.yes) if self.orderbook.yes else 0
        no_total = sum(q for _, q in self.orderbook.no) if self.orderbook.no else 0
        total = yes_total + no_total
        if total == 0:
            return None
        return (yes_total - no_total) / total

    def vwap_to_fill(self, side: str, size: int) -> Optional[float]:
        """Volume-weighted average price to fill `size` contracts.

        Args:
            side: "yes" or "no" - the side you're buying
            size: Number of contracts to fill

        Returns:
            VWAP in cents, or None if insufficient liquidity.
        """
        # To buy YES, you lift NO offers (sorted by price descending = best first)
        # To buy NO, you lift YES offers (sorted by price descending = best first)
        levels = self.orderbook.no if side == "yes" else self.orderbook.yes
        if not levels:
            return None

        # Sort by price descending (best offer = highest price for the other side)
        sorted_levels = sorted(levels, key=lambda x: x[0], reverse=True)

        remaining = size
        cost = 0
        for price, qty in sorted_levels:
            take = min(remaining, qty)
            # If buying YES, you pay (100 - no_price) per contract
            # If buying NO, you pay (100 - yes_price) per contract
            fill_price = 100 - price
            cost += take * fill_price
            remaining -= take
            if remaining <= 0:
                break

        if remaining > 0:
            return None  # Insufficient liquidity
        return cost / size


# --- Exchange Models ---

class ExchangeStatus(BaseModel):
    """Exchange operational status."""
    exchange_active: bool
    trading_active: bool

    model_config = ConfigDict(extra="ignore")


class Announcement(BaseModel):
    """Exchange announcement."""
    id: Optional[str] = None
    title: str
    body: Optional[str] = None
    type: Optional[str] = None
    created_time: Optional[str] = None
    delivery_time: Optional[str] = None
    status: Optional[str] = None

    model_config = ConfigDict(extra="ignore")


# --- Account Models ---

class RateLimitTier(BaseModel):
    """Rate limit for a specific tier."""
    max_requests: int
    period_seconds: int

    model_config = ConfigDict(extra="ignore")


class APILimits(BaseModel):
    """API rate limits for the authenticated user."""
    tier: Optional[str] = None
    limits: Optional[dict[str, RateLimitTier]] = None
    remaining: Optional[int] = None
    reset_at: Optional[int] = None

    model_config = ConfigDict(extra="ignore")


# --- API Key Models ---

class APIKey(BaseModel):
    """API key information."""
    id: str
    name: Optional[str] = None
    created_time: Optional[str] = None
    last_used: Optional[str] = None
    scopes: Optional[list[str]] = None

    model_config = ConfigDict(extra="ignore")


class GeneratedAPIKey(BaseModel):
    """Newly generated API key with private key (only returned once)."""
    id: str
    private_key: str
    name: Optional[str] = None

    model_config = ConfigDict(extra="ignore")


# --- Series & Trade Models ---

class SeriesModel(BaseModel):
    """Pydantic model for Series data."""
    ticker: str
    title: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[list[str]] = None
    settlement_timer_seconds: Optional[int] = None
    frequency: Optional[str] = None

    model_config = ConfigDict(extra="ignore")


class TradeModel(BaseModel):
    """Public trade execution record."""
    trade_id: str
    ticker: str
    count: int
    yes_price: int
    no_price: int
    taker_side: Optional[str] = None
    created_time: Optional[str] = None
    ts: Optional[int] = None

    model_config = ConfigDict(extra="ignore")


class SettlementModel(BaseModel):
    """Settlement record for a resolved position."""
    ticker: str
    event_ticker: Optional[str] = None
    market_result: Optional[str] = None  # "yes" or "no"
    yes_count: int = 0
    no_count: int = 0
    yes_total_cost: int = 0
    no_total_cost: int = 0
    revenue: int = 0  # Payout in cents
    value: int = 0
    fee_cost: Optional[str] = None  # Dollar string like "0.3200"
    settled_time: Optional[str] = None

    model_config = ConfigDict(extra="ignore")

    @property
    def net_position(self) -> int:
        """Net position: positive = yes, negative = no."""
        return self.yes_count - self.no_count

    @property
    def pnl(self) -> int:
        """Net P&L in cents (revenue - costs - fees)."""
        fee_cents = int(float(self.fee_cost or 0) * 100)
        return self.revenue - self.yes_total_cost - self.no_total_cost - fee_cents


class QueuePositionModel(BaseModel):
    """Order's position in the queue at its price level."""
    order_id: str
    queue_position: int  # 0-indexed position in queue

    model_config = ConfigDict(extra="ignore")


class OrderGroupModel(BaseModel):
    """Order group for linked order strategies (OCO, bracket)."""
    order_group_id: str
    status: Optional[str] = None  # "active", "triggered", "canceled"
    orders: Optional[list[str]] = None  # Order IDs in group
    created_time: Optional[str] = None

    model_config = ConfigDict(extra="ignore")


# --- Subaccount Models ---

class SubaccountModel(BaseModel):
    """Subaccount info."""
    subaccount_id: str
    subaccount_number: int
    created_time: Optional[str] = None

    model_config = ConfigDict(extra="ignore")


class SubaccountBalanceModel(BaseModel):
    """Balance for a single subaccount."""
    subaccount_id: str
    balance: int  # In cents
    portfolio_value: Optional[int] = None

    model_config = ConfigDict(extra="ignore")


class SubaccountTransferModel(BaseModel):
    """Record of a transfer between subaccounts."""
    transfer_id: str
    from_subaccount_id: str
    to_subaccount_id: str
    amount: int  # In cents
    created_time: Optional[str] = None

    model_config = ConfigDict(extra="ignore")


class ForecastPoint(BaseModel):
    """A single point in forecast percentile history."""
    ts: int  # Unix timestamp
    value: int  # Forecast value in cents

    model_config = ConfigDict(extra="ignore")


class ForecastPercentileHistory(BaseModel):
    """Historical forecast data at various percentiles for an event."""
    event_ticker: str
    percentiles: dict[str, list[ForecastPoint]]  # Maps percentile (e.g., "50") to history

    model_config = ConfigDict(extra="ignore")
