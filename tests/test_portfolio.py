"""Tests for portfolio functionality: positions, fills, and order retrieval."""

import pytest
from kalshi_api.enums import Action, Side, OrderStatus


def test_get_positions_workflow(client, mock_response, mocker):
    """Test fetching portfolio positions."""
    mock_get = mocker.patch(
        "requests.get",
        return_value=mock_response(
            {
                "market_positions": [
                    {
                        "ticker": "KXTEST-A",
                        "event_ticker": "KXTEST",
                        "position": 10,
                        "total_traded": 25,
                        "resting_orders_count": 2,
                        "fees_paid": 50,
                        "realized_pnl": 100,
                    },
                    {
                        "ticker": "KXTEST-B",
                        "event_ticker": "KXTEST",
                        "position": -5,
                        "total_traded": 10,
                        "resting_orders_count": 0,
                        "fees_paid": 25,
                        "realized_pnl": -30,
                    },
                ],
                "cursor": "",
            }
        ),
    )

    user = client.get_user()
    positions = user.get_positions()

    # Verify results
    assert len(positions) == 2
    assert positions[0].ticker == "KXTEST-A"
    assert positions[0].position == 10
    assert positions[1].position == -5  # Short position

    # Verify endpoint called
    mock_get.assert_called_with(
        "https://demo-api.elections.kalshi.com/trade-api/v2/portfolio/positions?limit=100",
        headers=mocker.ANY,
    )


def test_get_positions_with_filters(client, mock_response, mocker):
    """Test fetching positions with filters."""
    mock_get = mocker.patch(
        "requests.get",
        return_value=mock_response({"market_positions": [], "cursor": ""}),
    )

    user = client.get_user()
    user.get_positions(
        ticker="KXTEST-A", event_ticker="KXTEST", count_filter="position", limit=50
    )

    # Verify all filters passed in URL
    call_url = mock_get.call_args[0][0]
    assert "ticker=KXTEST-A" in call_url
    assert "event_ticker=KXTEST" in call_url
    assert "count_filter=position" in call_url
    assert "limit=50" in call_url


def test_get_fills_workflow(client, mock_response, mocker):
    """Test fetching trade fills."""
    mock_get = mocker.patch(
        "requests.get",
        return_value=mock_response(
            {
                "fills": [
                    {
                        "trade_id": "trade-001",
                        "ticker": "KXTEST",
                        "order_id": "order-123",
                        "side": "yes",
                        "action": "buy",
                        "count": 5,
                        "yes_price": 50,
                        "no_price": 50,
                        "created_time": "2024-01-01T12:00:00Z",
                        "is_taker": True,
                    },
                    {
                        "trade_id": "trade-002",
                        "ticker": "KXTEST",
                        "order_id": "order-124",
                        "side": "no",
                        "action": "sell",
                        "count": 3,
                        "yes_price": 45,
                        "no_price": 55,
                        "created_time": "2024-01-01T13:00:00Z",
                        "is_taker": False,
                    },
                ],
                "cursor": "",
            }
        ),
    )

    user = client.get_user()
    fills = user.get_fills()

    # Verify results
    assert len(fills) == 2
    assert fills[0].trade_id == "trade-001"
    assert fills[0].action == Action.BUY
    assert fills[0].side == Side.YES
    assert fills[0].count == 5
    assert fills[0].is_taker == True

    assert fills[1].action == Action.SELL
    assert fills[1].side == Side.NO

    # Verify endpoint called
    mock_get.assert_called_with(
        "https://demo-api.elections.kalshi.com/trade-api/v2/portfolio/fills?limit=100",
        headers=mocker.ANY,
    )


def test_get_fills_with_filters(client, mock_response, mocker):
    """Test fetching fills with filters."""
    mock_get = mocker.patch(
        "requests.get", return_value=mock_response({"fills": [], "cursor": ""})
    )

    user = client.get_user()
    user.get_fills(
        ticker="KXTEST",
        order_id="order-123",
        min_ts=1700000000,
        max_ts=1700100000,
        limit=25,
    )

    # Verify all filters in URL
    call_url = mock_get.call_args[0][0]
    assert "ticker=KXTEST" in call_url
    assert "order_id=order-123" in call_url
    assert "min_ts=1700000000" in call_url
    assert "max_ts=1700100000" in call_url
    assert "limit=25" in call_url


def test_get_order_by_id(client, mock_response, mocker):
    """Test fetching a single order by ID."""
    mock_get = mocker.patch(
        "requests.get",
        return_value=mock_response(
            {
                "order": {
                    "order_id": "order-abc-123",
                    "ticker": "KXTEST",
                    "action": "buy",
                    "side": "yes",
                    "count": 10,
                    "yes_price": 55,
                    "status": "resting",
                    "type": "limit",
                }
            }
        ),
    )

    user = client.get_user()
    order = user.get_order("order-abc-123")

    # Verify order data
    assert order.order_id == "order-abc-123"
    assert order.ticker == "KXTEST"
    assert order.status == OrderStatus.RESTING

    # Verify correct endpoint called
    mock_get.assert_called_with(
        "https://demo-api.elections.kalshi.com/trade-api/v2/portfolio/orders/order-abc-123",
        headers=mocker.ANY,
    )


def test_get_order_not_found(client, mock_response, mocker):
    """Test that 404 raises ResourceNotFoundError."""
    from kalshi_api.exceptions import ResourceNotFoundError

    mock_get = mocker.patch(
        "requests.get",
        return_value=mock_response(
            {"message": "Order not found", "code": "not_found"}, status_code=404
        ),
    )

    user = client.get_user()

    with pytest.raises(ResourceNotFoundError):
        user.get_order("nonexistent-order")
