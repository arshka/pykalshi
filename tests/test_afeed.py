"""Tests for AsyncFeed."""

import asyncio
from unittest.mock import AsyncMock

import pytest

from pykalshi import AsyncFeed, AsyncKalshiClient


@pytest.fixture
def async_client(mocker):
    """Returns an AsyncKalshiClient with mocked auth and HTTP session."""
    mocker.patch("pykalshi._base._BaseKalshiClient._load_private_key")
    mocker.patch(
        "pykalshi._base._BaseKalshiClient._sign_request",
        return_value=("1234567890", "fake_sig"),
    )
    mocker.patch("httpx.AsyncClient")
    return AsyncKalshiClient(
        api_key_id="fake_key",
        private_key_path="fake_path",
        demo=True,
    )


@pytest.mark.asyncio
async def test_subscribe_connected_sends_immediately(async_client):
    """subscribe() should send a live subscription when already connected."""
    feed = AsyncFeed(async_client)
    feed._connected = True
    feed._ws = object()
    feed._subscribe_and_track = AsyncMock()

    feed.subscribe("ticker", market_ticker="abc-123")
    await asyncio.sleep(0)

    feed._subscribe_and_track.assert_awaited_once_with(
        {"channels": ["ticker"], "market_ticker": "ABC-123"}
    )
