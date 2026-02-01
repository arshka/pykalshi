from __future__ import annotations
from typing import TYPE_CHECKING
from .orders import Order
from .enums import Action, Side, OrderType, OrderStatus
from .models import OrderModel, BalanceModel, PositionModel, FillModel

if TYPE_CHECKING:
    from .client import KalshiClient
    from .markets import Market


class Portfolio:
    """Authenticated user's portfolio and trading operations."""

    def __init__(self, client: KalshiClient) -> None:
        self.client = client

    @property
    def balance(self) -> BalanceModel:
        """Get portfolio balance. Values are in cents."""
        data = self.client.get("/portfolio/balance")
        return BalanceModel.model_validate(data)

    def place_order(
        self,
        ticker: str | Market,
        action: Action,
        side: Side,
        count: int,
        order_type: OrderType = OrderType.LIMIT,
        *,
        yes_price: int | None = None,
        no_price: int | None = None,
    ) -> Order:
        """Place an order on a market.

        Args:
            ticker: Market ticker string or Market object.
            action: BUY or SELL.
            side: YES or NO.
            count: Number of contracts.
            order_type: LIMIT or MARKET.
            yes_price: Price in cents (1-99) for the YES side.
            no_price: Price in cents (1-99) for the NO side.
                      Converted to yes_price internally (yes_price = 100 - no_price).
                      Provide exactly one of yes_price or no_price for limit orders.
        """
        if yes_price is not None and no_price is not None:
            raise ValueError("Specify yes_price or no_price, not both")
        if yes_price is None and no_price is None and order_type == OrderType.LIMIT:
            raise ValueError("Limit orders require yes_price or no_price")

        if no_price is not None:
            yes_price = 100 - no_price

        ticker_str = ticker if isinstance(ticker, str) else ticker.ticker

        order_data: dict = {
            "ticker": ticker_str,
            "action": action.value,
            "side": side.value,
            "count": count,
            "type": order_type.value,
        }
        if yes_price is not None:
            order_data["yes_price"] = yes_price

        response = self.client.post("/portfolio/orders", order_data)
        data = response.get("order", response)
        model = OrderModel.model_validate(data)
        return Order(self.client, model)

    def get_orders(
        self,
        status: OrderStatus | None = None,
        ticker: str | None = None,
        limit: int = 100,
        cursor: str | None = None,
        fetch_all: bool = False,
    ) -> list[Order]:
        """Get list of orders.

        Args:
            status: Filter by order status.
            ticker: Filter by market ticker.
            limit: Maximum results per page (default 100).
            cursor: Pagination cursor for fetching next page.
            fetch_all: If True, automatically fetch all pages.
        """
        params = {
            "limit": limit,
            "status": status.value if status is not None else None,
            "ticker": ticker,
            "cursor": cursor,
        }
        data = self.client.paginated_get("/portfolio/orders", "orders", params, fetch_all)
        return [Order(self.client, OrderModel.model_validate(d)) for d in data]

    def get_order(self, order_id: str) -> Order:
        """Get a single order by ID."""
        response = self.client.get(f"/portfolio/orders/{order_id}")
        data = response.get("order", response)
        model = OrderModel.model_validate(data)
        return Order(self.client, model)

    def get_positions(
        self,
        ticker: str | None = None,
        event_ticker: str | None = None,
        count_filter: str | None = None,
        limit: int = 100,
        cursor: str | None = None,
        fetch_all: bool = False,
    ) -> list[PositionModel]:
        """Get portfolio positions.

        Args:
            ticker: Filter by specific market ticker.
            event_ticker: Filter by event ticker.
            count_filter: Filter positions with non-zero values.
                         Options: "position", "total_traded", or both comma-separated.
            limit: Maximum positions per page (default 100, max 1000).
            cursor: Pagination cursor for fetching next page.
            fetch_all: If True, automatically fetch all pages.
        """
        params = {
            "limit": limit,
            "ticker": ticker,
            "event_ticker": event_ticker,
            "count_filter": count_filter,
            "cursor": cursor,
        }
        data = self.client.paginated_get("/portfolio/positions", "market_positions", params, fetch_all)
        return [PositionModel.model_validate(p) for p in data]

    def get_fills(
        self,
        ticker: str | None = None,
        order_id: str | None = None,
        min_ts: int | None = None,
        max_ts: int | None = None,
        limit: int = 100,
        cursor: str | None = None,
        fetch_all: bool = False,
    ) -> list[FillModel]:
        """Get trade fills (executed trades).

        Args:
            ticker: Filter by market ticker.
            order_id: Filter by specific order ID.
            min_ts: Minimum timestamp (Unix seconds).
            max_ts: Maximum timestamp (Unix seconds).
            limit: Maximum fills per page (default 100, max 200).
            cursor: Pagination cursor for fetching next page.
            fetch_all: If True, automatically fetch all pages.
        """
        params = {
            "limit": limit,
            "ticker": ticker,
            "order_id": order_id,
            "min_ts": min_ts,
            "max_ts": max_ts,
            "cursor": cursor,
        }
        data = self.client.paginated_get("/portfolio/fills", "fills", params, fetch_all)
        return [FillModel.model_validate(f) for f in data]
