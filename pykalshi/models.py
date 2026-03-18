from __future__ import annotations
from decimal import Decimal
from functools import cached_property
from typing import ClassVar, Callable
from pydantic import AliasChoices, BaseModel, ConfigDict, Field
from .enums import OrderStatus, Side, Action, OrderType, MarketStatus
from ._compat import CompatModel, dollars_to_cents, fp_to_int, orderbook_to_legacy, cents_to_dollars, _passthrough


class MveSelectedLeg(CompatModel):
    """A single leg in a multivariate event combo."""
    event_ticker: str
    market_ticker: str
    side: str  # "yes" or "no"
    yes_settlement_value_dollars: str | None = None

    _legacy_fields: ClassVar[dict[str, tuple[str, Callable]]] = {
        "yes_settlement_value": ("yes_settlement_value_dollars", dollars_to_cents),
    }

    model_config = ConfigDict(extra="ignore")


class MarketModel(CompatModel):
    """Pydantic model for Market data."""

    ticker: str
    event_ticker: str | None = None
    series_ticker: str | None = None
    market_type: str | None = None
    title: str | None = None
    subtitle: str | None = None
    yes_sub_title: str | None = None
    no_sub_title: str | None = None

    # Timing
    open_time: str | None = None
    close_time: str | None = None
    expiration_time: str | None = None
    expected_expiration_time: str | None = None
    latest_expiration_time: str | None = None
    created_time: str | None = None
    updated_time: str | None = None

    # Status & Result
    status: MarketStatus | None = None
    result: str | None = None
    settlement_value_dollars: str | None = None

    # Pricing (dollar strings, e.g. "0.45")
    yes_bid_dollars: str | None = None
    yes_ask_dollars: str | None = None
    no_bid_dollars: str | None = None
    no_ask_dollars: str | None = None
    last_price_dollars: str | None = None
    previous_yes_bid_dollars: str | None = None
    previous_yes_ask_dollars: str | None = None
    previous_price_dollars: str | None = None
    notional_value_dollars: str | None = None

    # Volume & Liquidity (fixed-point strings, e.g. "100.00")
    volume_fp: str | None = None
    volume_24h_fp: str | None = None
    open_interest_fp: str | None = None
    liquidity_dollars: str | None = None
    yes_bid_size_fp: str | None = None
    yes_ask_size_fp: str | None = None

    # Market structure
    tick_size: int | None = None
    price_level_structure: str | None = None
    fractional_trading_enabled: bool | None = None
    strike_type: str | None = None
    floor_strike: float | None = None
    cap_strike: float | None = None
    can_close_early: bool | None = None
    expiration_value: str | None = None
    settlement_timer_seconds: int | None = None
    rules_primary: str | None = None
    rules_secondary: str | None = None

    # Multivariate event (combo) fields
    mve_collection_ticker: str | None = None
    mve_selected_legs: list[MveSelectedLeg] | None = None
    is_provisional: bool | None = None

    _legacy_fields: ClassVar[dict[str, tuple[str, Callable]]] = {
        "settlement_value": ("settlement_value_dollars", dollars_to_cents),
        "yes_bid": ("yes_bid_dollars", dollars_to_cents),
        "yes_ask": ("yes_ask_dollars", dollars_to_cents),
        "no_bid": ("no_bid_dollars", dollars_to_cents),
        "no_ask": ("no_ask_dollars", dollars_to_cents),
        "last_price": ("last_price_dollars", dollars_to_cents),
        "previous_yes_bid": ("previous_yes_bid_dollars", dollars_to_cents),
        "previous_yes_ask": ("previous_yes_ask_dollars", dollars_to_cents),
        "previous_price": ("previous_price_dollars", dollars_to_cents),
        "notional_value": ("notional_value_dollars", dollars_to_cents),
        "tick_size_dollars": ("tick_size", cents_to_dollars),
        "volume": ("volume_fp", fp_to_int),
        "volume_24h": ("volume_24h_fp", fp_to_int),
        "open_interest": ("open_interest_fp", fp_to_int),
        "liquidity": ("liquidity_dollars", dollars_to_cents),
        "liquidity_fp": ("liquidity_dollars", _passthrough),
    }

    model_config = ConfigDict(extra="ignore")


class EventModel(BaseModel):
    """Pydantic model for Event data."""

    event_ticker: str
    series_ticker: str
    title: str | None = None
    sub_title: str | None = None
    category: str | None = None

    # Event properties
    mutually_exclusive: bool = False
    collateral_return_type: str | None = None

    # Timing
    strike_date: str | None = None
    strike_period: str | None = None

    # Availability
    available_on_brokers: bool = False

    model_config = ConfigDict(extra="ignore")


class OrderModel(CompatModel):
    """Pydantic model for Order data."""

    order_id: str
    ticker: str
    status: OrderStatus
    action: Action | None = None
    side: Side | None = None
    type: OrderType | None = None

    # Pricing (dollar strings)
    yes_price_dollars: str | None = None
    no_price_dollars: str | None = None

    # Counts (fixed-point strings)
    initial_count_fp: str | None = None
    fill_count_fp: str | None = None
    remaining_count_fp: str | None = None

    # Fees & costs (dollar strings)
    taker_fees_dollars: str | None = None
    maker_fees_dollars: str | None = None
    taker_fill_cost_dollars: str | None = None
    maker_fill_cost_dollars: str | None = None

    # Metadata
    user_id: str | None = None
    client_order_id: str | None = None
    created_time: str | None = None
    last_update_time: str | None = None
    expiration_time: str | None = None

    _legacy_fields: ClassVar[dict[str, tuple[str, Callable]]] = {
        "yes_price": ("yes_price_dollars", dollars_to_cents),
        "no_price": ("no_price_dollars", dollars_to_cents),
        "initial_count": ("initial_count_fp", fp_to_int),
        "fill_count": ("fill_count_fp", fp_to_int),
        "remaining_count": ("remaining_count_fp", fp_to_int),
        "taker_fees": ("taker_fees_dollars", dollars_to_cents),
        "maker_fees": ("maker_fees_dollars", dollars_to_cents),
        "taker_fill_cost": ("taker_fill_cost_dollars", dollars_to_cents),
        "maker_fill_cost": ("maker_fill_cost_dollars", dollars_to_cents),
    }

    model_config = ConfigDict(extra="ignore")


class BalanceModel(CompatModel):
    """Pydantic model for Balance data. Values are cents integers."""

    balance: int
    portfolio_value: int
    updated_ts: int | None = None

    _legacy_fields: ClassVar[dict[str, tuple[str, Callable]]] = {
        "balance_dollars": ("balance", cents_to_dollars),
        "portfolio_value_dollars": ("portfolio_value", cents_to_dollars),
    }

    model_config = ConfigDict(extra="ignore")

    def _repr_html_(self) -> str:
        from ._repr import balance_html
        return balance_html(self)


class PositionModel(CompatModel):
    """Pydantic model for a portfolio position."""

    ticker: str
    position_fp: str  # Net position (positive = yes, negative = no)
    market_exposure_dollars: str | None = None
    total_traded_dollars: str | None = None
    resting_orders_count: int | None = None
    fees_paid_dollars: str | None = None
    realized_pnl_dollars: str | None = None
    last_updated_ts: str | None = None

    _legacy_fields: ClassVar[dict[str, tuple[str, Callable]]] = {
        "position": ("position_fp", fp_to_int),
        "total_traded": ("total_traded_dollars", dollars_to_cents),
        "total_traded_fp": ("total_traded_dollars", _passthrough),
        "market_exposure": ("market_exposure_dollars", dollars_to_cents),
        "fees_paid": ("fees_paid_dollars", dollars_to_cents),
        "realized_pnl": ("realized_pnl_dollars", dollars_to_cents),
    }

    model_config = ConfigDict(extra="ignore")

    def _repr_html_(self) -> str:
        from ._repr import position_html
        return position_html(self)


class FillModel(CompatModel):
    """Pydantic model for a trade fill/execution."""

    trade_id: str
    ticker: str
    order_id: str
    side: Side
    action: Action
    count_fp: str
    yes_price_fixed: str
    no_price_fixed: str
    is_taker: bool | None = None
    fill_id: str | None = None
    market_ticker: str | None = None
    fee_cost: str | None = None
    created_time: str | None = None
    ts: int | None = None

    _legacy_fields: ClassVar[dict[str, tuple[str, Callable]]] = {
        "count": ("count_fp", fp_to_int),
        "yes_price": ("yes_price_fixed", dollars_to_cents),
        "no_price": ("no_price_fixed", dollars_to_cents),
        "fee_cost_dollars": ("fee_cost", _passthrough),
        "yes_price_dollars": ("yes_price_fixed", _passthrough),
        "no_price_dollars": ("no_price_fixed", _passthrough),
    }

    model_config = ConfigDict(extra="ignore")

    def _repr_html_(self) -> str:
        from ._repr import fill_html
        return fill_html(self)


class OHLCData(CompatModel):
    """OHLC price data (dollar strings)."""

    open_dollars: str | None = None
    high_dollars: str | None = None
    low_dollars: str | None = None
    close_dollars: str | None = None

    _legacy_fields: ClassVar[dict[str, tuple[str, Callable]]] = {
        "open": ("open_dollars", dollars_to_cents),
        "high": ("high_dollars", dollars_to_cents),
        "low": ("low_dollars", dollars_to_cents),
        "close": ("close_dollars", dollars_to_cents),
    }

    model_config = ConfigDict(extra="ignore")


class PriceData(CompatModel):
    """Price data with additional fields (dollar strings)."""

    open_dollars: str | None = None
    high_dollars: str | None = None
    low_dollars: str | None = None
    close_dollars: str | None = None
    max_dollars: str | None = None
    min_dollars: str | None = None
    mean_dollars: str | None = None
    previous_dollars: str | None = None

    _legacy_fields: ClassVar[dict[str, tuple[str, Callable]]] = {
        "open": ("open_dollars", dollars_to_cents),
        "high": ("high_dollars", dollars_to_cents),
        "low": ("low_dollars", dollars_to_cents),
        "close": ("close_dollars", dollars_to_cents),
        "max": ("max_dollars", dollars_to_cents),
        "min": ("min_dollars", dollars_to_cents),
        "mean": ("mean_dollars", dollars_to_cents),
        "previous": ("previous_dollars", dollars_to_cents),
    }

    model_config = ConfigDict(extra="ignore")


class Candlestick(CompatModel):
    """Pydantic model for a single Candlestick."""

    end_period_ts: int
    volume_fp: str | None = None
    open_interest_fp: str | None = None
    price: PriceData
    yes_bid: OHLCData | None = None
    yes_ask: OHLCData | None = None

    _legacy_fields: ClassVar[dict[str, tuple[str, Callable]]] = {
        "volume": ("volume_fp", fp_to_int),
        "open_interest": ("open_interest_fp", fp_to_int),
    }

    model_config = ConfigDict(extra="ignore")


class CandlestickResponse(BaseModel):
    """Pydantic model for Candlestick API response."""

    candlesticks: list[Candlestick]
    ticker: str = Field(validation_alias="market_ticker")

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    def to_dataframe(self):
        """Convert candlesticks to a pandas DataFrame.

        Requires pandas: pip install pykalshi[dataframe]

        Returns:
            DataFrame with columns: ticker, end_period_ts, timestamp,
            volume_fp, open_interest_fp, open_dollars, high_dollars,
            low_dollars, close_dollars, mean_dollars.
        """
        from .dataframe import to_dataframe
        return to_dataframe(self)


# Orderbook Models
class Orderbook(CompatModel):
    """Orderbook with yes/no price levels (dollar strings)."""

    yes_dollars: list[tuple[str, str | int]] | None = None  # [(price_dollars, quantity_fp), ...]
    no_dollars: list[tuple[str, str | int]] | None = None

    _legacy_fields: ClassVar[dict[str, tuple[str, Callable]]] = {
        "yes": ("yes_dollars", orderbook_to_legacy),
        "no": ("no_dollars", orderbook_to_legacy),
    }

    model_config = ConfigDict(extra="ignore")


class OrderbookResponse(BaseModel):
    """Pydantic model for the orderbook API response."""

    orderbook: Orderbook = Field(validation_alias=AliasChoices('orderbook', 'orderbook_fp'))

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    @cached_property
    def best_yes_bid(self) -> str | None:
        """Highest YES bid price (dollar string), or None if no bids."""
        if not self.orderbook.yes_dollars:
            return None
        return str(max(Decimal(p) for p, _ in self.orderbook.yes_dollars))

    @cached_property
    def best_no_bid(self) -> str | None:
        """Highest NO bid price (dollar string), or None if no bids."""
        if not self.orderbook.no_dollars:
            return None
        return str(max(Decimal(p) for p, _ in self.orderbook.no_dollars))

    @cached_property
    def best_yes_ask(self) -> str | None:
        """Lowest YES ask (= 1.00 - best NO bid), dollar string."""
        if self.best_no_bid is None:
            return None
        return str(Decimal("1") - Decimal(self.best_no_bid))

    @cached_property
    def spread(self) -> str | None:
        """Bid-ask spread in dollars. None if no two-sided market."""
        if self.best_yes_bid is None or self.best_yes_ask is None:
            return None
        return str(Decimal(self.best_yes_ask) - Decimal(self.best_yes_bid))

    @cached_property
    def mid(self) -> str | None:
        """Mid price (dollar string). None if no two-sided market."""
        if self.best_yes_bid is None or self.best_yes_ask is None:
            return None
        return str((Decimal(self.best_yes_bid) + Decimal(self.best_yes_ask)) / 2)

    @cached_property
    def spread_bps(self) -> float | None:
        """Spread as basis points of mid. None if no two-sided market."""
        if self.spread is None or self.mid is None:
            return None
        mid_d = Decimal(self.mid)
        if mid_d == 0:
            return None
        return float(Decimal(self.spread) / mid_d * 10000)

    def yes_depth(self, through_price: str) -> str:
        """Total YES bid quantity at or above `through_price` (dollar string)."""
        if not self.orderbook.yes_dollars:
            return "0"
        threshold = Decimal(through_price)
        total = sum(Decimal(q) for p, q in self.orderbook.yes_dollars if Decimal(p) >= threshold)
        return str(total)

    def no_depth(self, through_price: str) -> str:
        """Total NO bid quantity at or above `through_price` (dollar string)."""
        if not self.orderbook.no_dollars:
            return "0"
        threshold = Decimal(through_price)
        total = sum(Decimal(q) for p, q in self.orderbook.no_dollars if Decimal(p) >= threshold)
        return str(total)

    @cached_property
    def imbalance(self) -> float | None:
        """Order imbalance: (yes_depth - no_depth) / (yes_depth + no_depth). Range [-1, 1]."""
        yes_total = sum(Decimal(q) for _, q in self.orderbook.yes_dollars) if self.orderbook.yes_dollars else Decimal(0)
        no_total = sum(Decimal(q) for _, q in self.orderbook.no_dollars) if self.orderbook.no_dollars else Decimal(0)
        total = yes_total + no_total
        if total == 0:
            return None
        return float((yes_total - no_total) / total)

    def vwap_to_fill(self, side: str, size: str) -> str | None:
        """Volume-weighted average price to fill `size` contracts.

        Args:
            side: "yes" or "no" - the side you're buying
            size: Number of contracts to fill (fixed-point string)

        Returns:
            VWAP as dollar string, or None if insufficient liquidity.
        """
        # To buy YES, you lift NO offers (sorted by price descending = best first)
        # To buy NO, you lift YES offers (sorted by price descending = best first)
        levels = self.orderbook.no_dollars if side == "yes" else self.orderbook.yes_dollars
        if not levels:
            return None

        sorted_levels = sorted(levels, key=lambda x: Decimal(x[0]), reverse=True)

        remaining = Decimal(size)
        cost = Decimal(0)
        for price_str, qty_str in sorted_levels:
            price = Decimal(price_str)
            qty = Decimal(qty_str)
            take = min(remaining, qty)
            fill_price = Decimal("1") - price
            cost += take * fill_price
            remaining -= take
            if remaining <= 0:
                break

        if remaining > 0:
            return None
        return str(cost / Decimal(size))

    def to_dataframe(self):
        """Convert orderbook to a pandas DataFrame with price levels.

        Requires pandas: pip install pykalshi[dataframe]

        Returns:
            DataFrame with columns: side, price_dollars, quantity_fp.
            Sorted by side (yes first), then price descending.
        """
        from .dataframe import to_dataframe
        return to_dataframe(self)

    def _repr_html_(self) -> str:
        from ._repr import orderbook_html
        return orderbook_html(self)


# --- Exchange Models ---

class ExchangeStatus(BaseModel):
    """Exchange operational status."""
    exchange_active: bool
    trading_active: bool

    model_config = ConfigDict(extra="ignore")

    def _repr_html_(self) -> str:
        from ._repr import exchange_status_html
        return exchange_status_html(self)


class Announcement(BaseModel):
    """Exchange announcement."""
    id: str | None = None
    title: str
    body: str | None = None
    type: str | None = None
    created_time: str | None = None
    delivery_time: str | None = None
    status: str | None = None

    model_config = ConfigDict(extra="ignore")

    def _repr_html_(self) -> str:
        from ._repr import announcement_html
        return announcement_html(self)


# --- Account Models ---

class RateLimitTier(BaseModel):
    """Rate limit for a specific tier."""
    max_requests: int
    period_seconds: int

    model_config = ConfigDict(extra="ignore")


class APILimits(BaseModel):
    """API rate limits for the authenticated user."""
    usage_tier: str | None = None
    read_limit: int | None = None
    write_limit: int | None = None

    model_config = ConfigDict(extra="ignore")

    def _repr_html_(self) -> str:
        from ._repr import api_limits_html
        return api_limits_html(self)


# --- API Key Models ---

class APIKey(BaseModel):
    """API key information."""
    id: str = Field(validation_alias="api_key_id")
    name: str | None = None
    created_time: str | None = None
    last_used: str | None = None
    scopes: list[str] | None = None

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    def _repr_html_(self) -> str:
        from ._repr import api_key_html
        return api_key_html(self)


class GeneratedAPIKey(BaseModel):
    """Newly generated API key with private key (only returned once)."""
    id: str = Field(validation_alias="api_key_id")
    private_key: str
    name: str | None = None

    model_config = ConfigDict(extra="ignore", populate_by_name=True)


# --- Series & Trade Models ---

class SeriesModel(BaseModel):
    """Pydantic model for Series data."""
    ticker: str
    title: str | None = None
    category: str | None = None
    tags: list[str] | None = None
    settlement_timer_seconds: int | None = None
    frequency: str | None = None

    model_config = ConfigDict(extra="ignore")


class TradeModel(CompatModel):
    """Public trade execution record."""
    trade_id: str
    ticker: str
    count_fp: str
    yes_price_dollars: str
    no_price_dollars: str
    taker_side: str | None = None
    created_time: str | None = None
    ts: int | None = None

    _legacy_fields: ClassVar[dict[str, tuple[str, Callable]]] = {
        "count": ("count_fp", fp_to_int),
        "yes_price": ("yes_price_dollars", dollars_to_cents),
        "no_price": ("no_price_dollars", dollars_to_cents),
    }

    model_config = ConfigDict(extra="ignore")

    def _repr_html_(self) -> str:
        from ._repr import trade_html
        return trade_html(self)


class SettlementModel(CompatModel):
    """Settlement record for a resolved position."""
    ticker: str
    event_ticker: str | None = None
    market_result: str | None = None  # "yes" or "no"
    yes_count_fp: str = "0"
    no_count_fp: str = "0"
    yes_total_cost: int = 0
    no_total_cost: int = 0
    revenue: int = 0
    value: int = 0
    fee_cost: str | None = None  # FixedPointDollars string (e.g. "0.3200")
    settled_time: str | None = None

    _legacy_fields: ClassVar[dict[str, tuple[str, Callable]]] = {
        "yes_count": ("yes_count_fp", fp_to_int),
        "no_count": ("no_count_fp", fp_to_int),
        "yes_total_cost_dollars": ("yes_total_cost", cents_to_dollars),
        "no_total_cost_dollars": ("no_total_cost", cents_to_dollars),
        "revenue_dollars": ("revenue", cents_to_dollars),
        "value_dollars": ("value", cents_to_dollars),
        "fee_cost_dollars": ("fee_cost", _passthrough),
    }

    model_config = ConfigDict(extra="ignore")

    @property
    def net_position(self) -> str:
        """Net position: positive = yes, negative = no (fixed-point string)."""
        return str(Decimal(self.yes_count_fp) - Decimal(self.no_count_fp))

    @property
    def pnl(self) -> int:
        """Net P&L in cents (revenue - costs - fees)."""
        fee_cents = round(float(self.fee_cost or 0) * 100)
        return self.revenue - self.yes_total_cost - self.no_total_cost - fee_cents

    def _repr_html_(self) -> str:
        from ._repr import settlement_html
        return settlement_html(self)


class QueuePositionModel(CompatModel):
    """Order's position in the queue at its price level."""
    order_id: str
    queue_position_fp: str  # 0-indexed, fixed-point string (e.g. "0.00")

    _legacy_fields: ClassVar[dict[str, tuple[str, Callable]]] = {
        "queue_position": ("queue_position_fp", fp_to_int),
    }

    def _repr_html_(self) -> str:
        from ._repr import queue_position_html
        return queue_position_html(self)


class OrderGroupModel(CompatModel):
    """Order group for rate-limiting contract matches.

    Order groups limit total contracts matched across all orders in the group
    over a rolling 15-second window. When the limit is hit, all orders in the
    group are cancelled.
    """
    # API returns 'id' in list/get, but 'order_group_id' in create response
    id: str = Field(validation_alias=AliasChoices('id', 'order_group_id'))
    is_auto_cancel_enabled: bool | None = None
    contracts_limit_fp: str | None = None
    # Only returned from get_order_group (not list)
    orders: list[str] | None = None

    _legacy_fields: ClassVar[dict[str, tuple[str, Callable]]] = {
        "contracts_limit": ("contracts_limit_fp", fp_to_int),
    }

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    def _repr_html_(self) -> str:
        from ._repr import order_group_html
        return order_group_html(self)


# --- Subaccount Models ---

class SubaccountModel(BaseModel):
    """Subaccount info."""
    subaccount_id: str
    subaccount_number: int
    created_time: str | None = None

    model_config = ConfigDict(extra="ignore")


class SubaccountBalanceModel(CompatModel):
    """Balance for a single subaccount."""
    subaccount_id: str
    balance_dollars: str
    portfolio_value_dollars: str | None = None

    _legacy_fields: ClassVar[dict[str, tuple[str, Callable]]] = {
        "balance": ("balance_dollars", dollars_to_cents),
        "portfolio_value": ("portfolio_value_dollars", dollars_to_cents),
    }

    model_config = ConfigDict(extra="ignore")


class SubaccountTransferModel(CompatModel):
    """Record of a transfer between subaccounts."""
    transfer_id: str
    from_subaccount_id: str
    to_subaccount_id: str
    amount_dollars: str
    created_time: str | None = None

    _legacy_fields: ClassVar[dict[str, tuple[str, Callable]]] = {
        "amount": ("amount_dollars", dollars_to_cents),
    }

    model_config = ConfigDict(extra="ignore")


class ForecastPoint(CompatModel):
    """A single point in forecast percentile history."""
    ts: int  # Unix timestamp
    value_dollars: str  # Forecast value as dollar string

    _legacy_fields: ClassVar[dict[str, tuple[str, Callable]]] = {
        "value": ("value_dollars", dollars_to_cents),
    }

    model_config = ConfigDict(extra="ignore")


class ForecastPercentileHistory(BaseModel):
    """Historical forecast data at various percentiles for an event."""
    event_ticker: str
    percentiles: dict[str, list[ForecastPoint]]  # Maps percentile (e.g., "50") to history

    model_config = ConfigDict(extra="ignore")


# --- Multivariate Event Collection Models ---

class AssociatedEventModel(CompatModel):
    """An event available as a leg in a multivariate event collection."""
    ticker: str
    is_yes_only: bool = False
    size_min_fp: str | None = None
    size_max_fp: str | None = None
    active_quoters: list[str] | None = None

    _legacy_fields: ClassVar[dict[str, tuple[str, Callable]]] = {
        "size_min": ("size_min_fp", fp_to_int),
        "size_max": ("size_max_fp", fp_to_int),
    }

    model_config = ConfigDict(extra="ignore")


class MveCollectionModel(CompatModel):
    """Pydantic model for a multivariate event collection (combo container)."""
    collection_ticker: str
    series_ticker: str | None = None
    title: str | None = None
    description: str | None = None
    open_date: str | None = None
    close_date: str | None = None
    associated_events: list[AssociatedEventModel] | None = None
    is_ordered: bool = False
    size_min_fp: str | None = None
    size_max_fp: str | None = None
    functional_description: str | None = None

    _legacy_fields: ClassVar[dict[str, tuple[str, Callable]]] = {
        "size_min": ("size_min_fp", fp_to_int),
        "size_max": ("size_max_fp", fp_to_int),
    }

    model_config = ConfigDict(extra="ignore")


# --- Communications Models (RFQ / Quotes) ---

class RfqModel(CompatModel):
    """Request for Quote on a multivariate event combo."""
    rfq_id: str = Field(validation_alias=AliasChoices('rfq_id', 'id'))
    market_ticker: str | None = None
    status: str | None = None
    contracts_fp: str | None = None
    target_cost_dollars: str | None = None
    rest_remainder: bool | None = None
    mve_collection_ticker: str | None = None
    mve_selected_legs: list[MveSelectedLeg] | None = None
    created_ts: str | None = None
    expiration_time: str | None = None
    creator_id: str | None = None

    _legacy_fields: ClassVar[dict[str, tuple[str, Callable]]] = {
        "contracts": ("contracts_fp", fp_to_int),
        "target_cost": ("target_cost_dollars", dollars_to_cents),
    }

    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class QuoteModel(CompatModel):
    """A quote in response to an RFQ."""
    quote_id: str = Field(validation_alias=AliasChoices('quote_id', 'id'))
    rfq_id: str | None = None
    market_ticker: str | None = None
    status: str | None = None
    yes_bid_dollars: str | None = None
    no_bid_dollars: str | None = None
    rest_remainder: bool | None = None
    created_ts: str | None = None
    expiration_time: str | None = None
    creator_id: str | None = None

    _legacy_fields: ClassVar[dict[str, tuple[str, Callable]]] = {
        "yes_bid": ("yes_bid_dollars", dollars_to_cents),
        "no_bid": ("no_bid_dollars", dollars_to_cents),
    }

    model_config = ConfigDict(extra="ignore", populate_by_name=True)
