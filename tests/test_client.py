import pytest
from unittest.mock import MagicMock
from kalshi_api import KalshiClient
from kalshi_api.exceptions import (
    AuthenticationError,
    InsufficientFundsError,
    ResourceNotFoundError,
    KalshiAPIError,
)


def test_auth_headers_generated(client, mock_response, mocker):
    """Verify headers include signature."""
    requests_get = mocker.patch("requests.get", return_value=mock_response({}))

    client.get("/test")

    # Check headers
    call_args = requests_get.call_args
    headers = call_args[1]["headers"]
    assert "KALSHI-ACCESS-KEY" in headers
    assert "KALSHI-ACCESS-SIGNATURE" in headers
    assert headers["KALSHI-ACCESS-KEY"] == "fake_key"


def test_handle_success(client, mock_response, mocker):
    """Verify successful response returns JSON."""
    mocker.patch("requests.get", return_value=mock_response({"data": "ok"}))
    resp = client.get("/test")
    assert resp == {"data": "ok"}


def test_handle_401_raises_auth_error(client, mock_response, mocker):
    """Verify 401 raises AuthenticationError."""
    mocker.patch(
        "requests.get",
        return_value=mock_response({"message": "Unauthorized"}, status_code=401),
    )
    with pytest.raises(AuthenticationError):
        client.get("/test")


def test_handle_404_raises_not_found(client, mock_response, mocker):
    """Verify 404 raises ResourceNotFoundError."""
    mocker.patch(
        "requests.get",
        return_value=mock_response({"message": "Not Found"}, status_code=404),
    )
    with pytest.raises(ResourceNotFoundError):
        client.get("/test")


def test_insufficient_funds_error(client, mock_response, mocker):
    """Verify specific error code raises InsufficientFundsError."""
    mocker.patch(
        "requests.post",
        return_value=mock_response(
            {"code": "insufficient_funds", "message": "No money"}, status_code=400
        ),
    )
    with pytest.raises(InsufficientFundsError):
        client.post("/orders", {})

    # Test alternate code "insufficient_balance"
    mocker.patch(
        "requests.post",
        return_value=mock_response({"code": "insufficient_balance"}, status_code=400),
    )
    with pytest.raises(InsufficientFundsError):
        client.post("/orders", {})
