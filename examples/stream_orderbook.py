"""WebSocket streaming example: real-time market data.

This example shows how to subscribe to live market updates via WebSocket.

Setup:
    1. Create a .env file with your credentials
    2. Run: python examples/stream_orderbook.py
"""

import asyncio
from pykalshi import KalshiClient, Feed, OrderbookManager

# Initialize client
client = KalshiClient()


async def stream_ticker():
    """Stream live ticker updates for a market."""
    print("Streaming ticker updates (Ctrl+C to stop)...\n")

    async with Feed(client) as feed:
        # Subscribe to a market ticker
        # Replace with an active market ticker
        await feed.subscribe_ticker("INXD-25FEB03-B5975")

        async for msg in feed:
            print(f"[{msg.__class__.__name__}] {msg}")


async def stream_orderbook():
    """Stream and maintain a local orderbook."""
    print("Streaming orderbook (Ctrl+C to stop)...\n")

    # OrderbookManager maintains local state from WebSocket updates
    manager = OrderbookManager()

    async with Feed(client) as feed:
        ticker = "INXD-25FEB03-B5975"  # Replace with active ticker
        await feed.subscribe_orderbook(ticker)

        async for msg in feed:
            # Update local orderbook state
            manager.apply(msg)

            # Get current state
            book = manager.get(ticker)
            if book:
                best_bid = book["yes"][0] if book["yes"] else None
                best_ask = book["no"][0] if book["no"] else None
                print(f"Best bid: {best_bid}, Best ask: {best_ask}")


async def stream_trades():
    """Stream public trades."""
    print("Streaming trades (Ctrl+C to stop)...\n")

    async with Feed(client) as feed:
        await feed.subscribe_trades("INXD-25FEB03-B5975")

        async for msg in feed:
            print(f"Trade: {msg.count}x @ {msg.yes_price}¢ ({msg.taker_side})")


async def stream_multiple():
    """Subscribe to multiple data types at once."""
    print("Streaming multiple channels (Ctrl+C to stop)...\n")

    async with Feed(client) as feed:
        ticker = "INXD-25FEB03-B5975"

        # Subscribe to multiple channels
        await feed.subscribe_ticker(ticker)
        await feed.subscribe_orderbook(ticker)
        await feed.subscribe_trades(ticker)

        async for msg in feed:
            # Messages are typed - handle each type differently
            print(f"[{msg.__class__.__name__}] {msg.market_ticker}")


async def stream_portfolio():
    """Stream your own fills and position updates (private channel)."""
    print("Streaming portfolio updates (Ctrl+C to stop)...\n")

    async with Feed(client) as feed:
        # Subscribe to your fills
        await feed.subscribe_fills()

        async for msg in feed:
            print(f"Fill: {msg.action} {msg.count}x {msg.ticker} @ {msg.yes_price}¢")


if __name__ == "__main__":
    # Choose which stream to run:
    asyncio.run(stream_ticker())
    # asyncio.run(stream_orderbook())
    # asyncio.run(stream_trades())
    # asyncio.run(stream_multiple())
    # asyncio.run(stream_portfolio())
