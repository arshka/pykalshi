import pytest
import requests
from kalshi_api.enums import Action, Side, OrderType, OrderStatus


def test_user_balance_workflow(client, mock_response, mocker):
    """Test fetching user balance."""
    mock_get = mocker.patch(
        "requests.get",
        return_value=mock_response({"balance": 5000, "portfolio_value": 10000}),
    )

    balance = client.portfolio.balance

    # Verify values
    assert balance.balance == 5000
    assert balance.portfolio_value == 10000

    # Verify endpoint called
    mock_get.assert_called_with(
        "https://demo-api.elections.kalshi.com/trade-api/v2/portfolio/balance",
        headers=mocker.ANY,
        timeout=mocker.ANY,
    )


def test_place_order_workflow(client, mock_response, mocker):
    """Test placing an order via Portfolio object."""
    # Mock response for successful order placement
    mock_post = mocker.patch(
        "requests.post",
        return_value=mock_response(
            {
                "order": {
                    "order_id": "bfs-123",
                    "ticker": "KXTEST",
                    "action": "buy",
                    "side": "yes",
                    "count": 5,
                    "price": 50,
                    "status": "resting",
                    "created_time": "2023-01-01T00:00:00Z",
                }
            }
        ),
    )

    # Mock Market object (just need ticker)
    market = mocker.MagicMock()
    market.ticker = "KXTEST"

    order = client.portfolio.place_order(
        market, action=Action.BUY, side=Side.YES, count=5, yes_price=50
    )

    # Verify Order object returned (delegated through __getattr__)
    assert order.order_id == "bfs-123"
    assert order.status == OrderStatus.RESTING

    # Verify correct payload sent
    mock_post.assert_called_once()
    call_args = mock_post.call_args
    assert (
        "https://demo-api.elections.kalshi.com/trade-api/v2/portfolio/orders"
        in call_args[0]
    )
    import json

    body = json.loads(call_args[1]["data"])
    assert body["ticker"] == "KXTEST"
    assert body["action"] == "buy"
    assert body["side"] == "yes"
    assert body["count"] == 5
    assert body["yes_price"] == 50


def test_market_orderbook_workflow(client, mock_response, mocker):
    """Test fetching orderbook via Market object."""
    mock_get = mocker.patch("requests.get")
    mock_get.side_effect = [
        # Call 1: Market data
        mock_response(
            {
                "market": {
                    "ticker": "KXTEST",
                    "title": "Test Market",
                    "status": "open",
                    "yes_bid": 10,
                    "yes_ask": 12,
                    "expiration_time": "2024-01-01T00:00:00Z",
                }
            }
        ),
        # Call 2: Orderbook data
        mock_response({"orderbook": {"yes": [[10, 50]], "no": [[90, 50]]}}),
    ]

    # 1. Fetch market
    market = client.get_market("KXTEST")

    # 2. Fetch orderbook
    ob = market.get_orderbook()

    # Verify typed OrderbookResponse
    assert ob.orderbook.yes == [(10, 50)]
    assert ob.best_yes_bid == 10
    assert mock_get.call_count == 2

    # Verify URL of second call
    call_args_list = mock_get.call_args_list
    assert "/markets/KXTEST/orderbook" in call_args_list[1][0][0]
