# Kalshi API Documentation

## Overview

The `kalshi_api` library provides a strictly typed, object-oriented interface for the Kalshi Trading API.

## Core Classes

### `KalshiClient`

The entry point for all API interactions.

**Constructor:**
```python
client = KalshiClient(
    api_key_id="...",          # Optional (defaults to env var)
    private_key_path="...",    # Optional (defaults to env var)
    api_base="...",            # Optional (custom API base URL)
    demo=False                 # Set True to use demo.kalshi.com
)
```

**Methods:**
- `get_user() -> User`: Returns the authenticated user session.
- `get_market(ticker: str) -> Market`: Fetch a single market by ticker.
- `get_markets(...) -> list[Market]`: Search for markets.
  - `series_ticker`: Filter by series.
  - `event_ticker`: Filter by event.
  - `status`: Market status (default: `"open"`).
  - `limit`: Max results (default: `100`).

---

### `User`

Represents your authenticated session and portfolio.

**Properties:**
- `balance -> BalanceModel`: Returns account balance details.
    - `balance.balance`: Cash balance in cents.
    - `balance.portfolio_value`: Total portfolio value in cents.

**Methods:**
- `place_order(market, action, side, count, price, order_type) -> Order`: Place a new order.
- `get_orders(status: str | None) -> list[Order]`: List your orders.
- `get_order(order_id: str) -> Order`: Get a single order by ID.
- `get_positions(...) -> list[PositionModel]`: Get portfolio positions.
  - `ticker`: Filter by market ticker.
  - `event_ticker`: Filter by event.
  - `count_filter`: Filter positions (`"position"`, `"total_traded"`).
  - `limit`: Max results (default: `100`).
- `get_fills(...) -> list[FillModel]`: Get trade fills (executed trades).
  - `ticker`: Filter by market ticker.
  - `order_id`: Filter by order ID.
  - `min_ts` / `max_ts`: Timestamp range (Unix seconds).
  - `limit`: Max results (default: `100`).

---

### `Market`

Represents a prediction market contract.

**Attributes:**
- `ticker`: Unique identifier (e.g., `"KXHIGHNY-25DEC15-T33"`).
- `series_ticker`: Series identifier for the market.
- `event_ticker`: Event identifier.
- `title`: Human-readable title.
- `yes_bid` / `yes_ask`: Current best prices for "Yes".

**Methods:**
- `get_orderbook() -> dict`: Fetch current bids/asks.
- `get_candlesticks(start_ts, end_ts, period) -> CandlestickResponse`: Fetch historical candlestick data.
  - `start_ts`: Start timestamp (Unix seconds).
  - `end_ts`: End timestamp (Unix seconds).
  - `period`: `CandlestickPeriod` enum (default: `ONE_HOUR`).

---

### `Order`

Represents a trade order.

**Attributes:**
- `order_id`: Unique UUID.
- `status`: `OrderStatus` (e.g., `RESTING`, `FILLED`).
- `ticker`: Market ticker.

**Methods:**
- `cancel() -> OrderModel`: Cancels the order.

---

## Enums

Use these strict types for API interactions.

### `Action`
- `Action.BUY`
- `Action.SELL`

### `Side`
- `Side.YES`
- `Side.NO`

### `OrderType`
- `OrderType.LIMIT`
- `OrderType.MARKET`

### `OrderStatus`
- `OrderStatus.RESTING`
- `OrderStatus.CANCELED`
- `OrderStatus.FILLED`
- `OrderStatus.EXECUTED`

### `CandlestickPeriod`
- `CandlestickPeriod.ONE_MINUTE` (1 minute)
- `CandlestickPeriod.ONE_HOUR` (60 minutes)
- `CandlestickPeriod.ONE_DAY` (1440 minutes)

---

## Models (Pydantic)

These are the data models returned by API methods.

### `BalanceModel`
- `balance: int` — Cash balance in cents.
- `portfolio_value: int` — Total portfolio value in cents.

### `MarketModel`
- `ticker`, `series_ticker`, `event_ticker`, `title`
- `open_time`, `close_time`, `expiration_time`, `created_time`
- `status`, `result`, `settlement_value`
- `yes_bid`, `yes_ask`, `no_bid`, `no_ask`, `last_price`
- `volume`, `volume_24h`, `open_interest`, `liquidity`

### `OrderModel`
- `order_id`, `ticker`, `status`
- `action`, `side`, `count`, `yes_price`, `type`

### `PositionModel`
- `ticker`, `event_ticker`, `event_exposure`
- `position`: Net position (positive = yes, negative = no).
- `total_traded`, `resting_orders_count`, `fees_paid`, `realized_pnl`

### `FillModel`
- `trade_id`, `ticker`, `order_id`
- `side`, `action`, `count`
- `yes_price`, `no_price`
- `created_time`, `is_taker`

### `CandlestickResponse`
- `ticker: str`
- `candlesticks: list[Candlestick]`

### `Candlestick`
- `end_period_ts: int` — End of period timestamp.
- `volume: int`
- `open_interest: int`
- `price: PriceData`
- `yes_bid: OHLCData` (optional)
- `yes_ask: OHLCData` (optional)

### `PriceData`
- `open`, `high`, `low`, `close`
- `max`, `min`, `mean`, `previous`

### `OHLCData`
- `open`, `high`, `low`, `close`
- `open_dollars`, `high_dollars`, `low_dollars`, `close_dollars`

---

## Error Handling

All API errors raise exceptions inheriting from `KalshiAPIError`.

```python
from kalshi_api.exceptions import (
    KalshiAPIError,
    AuthenticationError,
    InsufficientFundsError,
    ResourceNotFoundError,
)

try:
    user.place_order(...)
except InsufficientFundsError:
    print("Not enough money!")
except AuthenticationError:
    print("Check your keys!")
except ResourceNotFoundError:
    print("Market or order not found!")
except KalshiAPIError as e:
    print(f"API Error {e.status_code}: {e.error_code}")
```

### Exception Hierarchy
- `KalshiError` — Base exception.
  - `KalshiAPIError` — API returned non-200 response.
    - `AuthenticationError` — 401/403 responses.
    - `InsufficientFundsError` — Insufficient balance.
    - `ResourceNotFoundError` — 404 responses.
