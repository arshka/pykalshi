from __future__ import annotations
from typing import TYPE_CHECKING
from .orders import Order
from .enums import Action, Side, OrderType
from .models import OrderModel, BalanceModel, PositionModel, FillModel

if TYPE_CHECKING:
    from .client import KalshiClient
    from .markets import Market


class User:
    """
    Represents the authenticated Kalshi user/account.
    """

    def __init__(self, client: KalshiClient):
        self.client = client
        self._balance_cache = None

    @property
    def balance(self) -> BalanceModel:
        """
        Get portfolio balance.
        Returns BalanceModel with 'balance' and 'portfolio_value' in cents.
        """
        data = self.client.get("/portfolio/balance")
        return BalanceModel.model_validate(data)

    def place_order(
        self,
        market: Market,
        action: Action,
        side: Side,
        count: int,
        price: int,
        order_type: OrderType = OrderType.LIMIT,
    ) -> Order:
        """
        Place an order on a specific market.
        """
        order_data = {
            "ticker": market.ticker,
            "action": action.value,
            "side": side.value,
            "count": count,
            "type": order_type.value,
            "yes_price": price,
        }
        response = self.client.post("/portfolio/orders", order_data)
        data = response.get("order", response)
        # Validate logic
        model = OrderModel.model_validate(data)
        return Order(self.client, model)

    def get_orders(self, status: str | None = None) -> list[Order]:
        """
        Get list of orders.
        """
        endpoint = "/portfolio/orders"
        if status:
            endpoint += f"?status={status}"
        response = self.client.get(endpoint)
        orders_data = response.get("orders", [])
        # Validate data
        return [Order(self.client, OrderModel.model_validate(d)) for d in orders_data]

    def get_order(self, order_id: str) -> Order:
        """
        Get a single order by ID.

        Args:
            order_id: The unique order identifier.

        Returns:
            Order object for the specified order.
        """
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
    ) -> list[PositionModel]:
        """
        Get portfolio positions.

        Args:
            ticker: Filter by specific market ticker.
            event_ticker: Filter by event ticker.
            count_filter: Filter positions with non-zero values.
                         Options: "position", "total_traded", or both comma-separated.
            limit: Maximum number of positions to return (default 100).

        Returns:
            List of PositionModel objects representing portfolio holdings.
        """
        params = [f"limit={limit}"]
        if ticker:
            params.append(f"ticker={ticker}")
        if event_ticker:
            params.append(f"event_ticker={event_ticker}")
        if count_filter:
            params.append(f"count_filter={count_filter}")

        endpoint = f"/portfolio/positions?{'&'.join(params)}"
        response = self.client.get(endpoint)
        positions_data = response.get("market_positions", [])
        return [PositionModel.model_validate(p) for p in positions_data]

    def get_fills(
        self,
        ticker: str | None = None,
        order_id: str | None = None,
        min_ts: int | None = None,
        max_ts: int | None = None,
        limit: int = 100,
    ) -> list[FillModel]:
        """
        Get trade fills (executed trades).

        Args:
            ticker: Filter by market ticker.
            order_id: Filter by specific order ID.
            min_ts: Minimum timestamp (Unix timestamp in seconds).
            max_ts: Maximum timestamp (Unix timestamp in seconds).
            limit: Maximum number of fills to return (default 100).

        Returns:
            List of FillModel objects representing executed trades.
        """
        params = [f"limit={limit}"]
        if ticker:
            params.append(f"ticker={ticker}")
        if order_id:
            params.append(f"order_id={order_id}")
        if min_ts:
            params.append(f"min_ts={min_ts}")
        if max_ts:
            params.append(f"max_ts={max_ts}")

        endpoint = f"/portfolio/fills?{'&'.join(params)}"
        response = self.client.get(endpoint)
        fills_data = response.get("fills", [])
        return [FillModel.model_validate(f) for f in fills_data]
