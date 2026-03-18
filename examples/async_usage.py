"""Async usage example: the same operations as basic_usage.py, but async.

Shows how to use AsyncKalshiClient and AsyncFeed for non-blocking I/O,
useful when integrating with other async code (web servers, bots, etc).

Setup:
    1. Create a .env file with your credentials:
       KALSHI_API_KEY_ID=your-key-id
       KALSHI_PRIVATE_KEY_PATH=/path/to/private-key.key

    2. Run: python examples/async_usage.py
"""

import asyncio

from pykalshi import AsyncKalshiClient, MarketStatus, TickerMessage


async def browse_markets():
    """Browse markets and check portfolio — async version."""
    async with AsyncKalshiClient.from_env() as client:
        # Portfolio
        balance = await client.portfolio.get_balance()
        print(f"Balance: ${balance.balance / 100:.2f}")

        positions = await client.portfolio.get_positions()
        print(f"Open positions: {len(positions)}")
        for pos in positions[:5]:
            print(f"  {pos.ticker}: {pos.position_fp} contracts")

        # Markets
        markets = await client.get_markets(status=MarketStatus.OPEN, limit=5)
        print(f"\n{len(markets)} open markets:")
        for market in markets:
            print(f"  {market.ticker}: {market.yes_bid_dollars}/{market.yes_ask_dollars}")

        # Navigation — async domain objects use await
        if markets:
            event = await markets[0].get_event()
            print(f"\nEvent: {event.title}")


async def stream_prices():
    """Stream live prices using AsyncFeed — no threads needed."""
    client = AsyncKalshiClient.from_env()

    # Pick a market to stream
    markets = await client.get_markets(status=MarketStatus.OPEN, limit=10)
    if not markets:
        print("No open markets")
        return

    market = max(markets, key=lambda m: float(m.volume_fp or "0"))
    print(f"Streaming {market.ticker}: {market.title}\n")

    async with client.feed() as feed:
        @feed.on("ticker")
        def handle(msg: TickerMessage):
            print(f"  {msg.market_ticker}: {msg.yes_bid_dollars}/{msg.yes_ask_dollars} (vol: {msg.volume_fp})")

        feed.subscribe("ticker", market_ticker=market.ticker)

        # async for drives the feed — no time.sleep loop needed
        count = 0
        async for msg in feed:
            count += 1
            if count >= 20:  # Stop after 20 messages for demo
                break

    await client.aclose()
    print("\nDone.")


async def parallel_requests():
    """Fetch multiple markets concurrently with asyncio.gather."""
    async with AsyncKalshiClient.from_env() as client:
        markets = await client.get_markets(status=MarketStatus.OPEN, limit=3)
        if not markets:
            return

        # Fetch orderbooks in parallel
        orderbooks = await asyncio.gather(
            *(m.get_orderbook() for m in markets)
        )

        for market, ob in zip(markets, orderbooks):
            yes_levels = len(ob.orderbook.yes_dollars or [])
            no_levels = len(ob.orderbook.no_dollars or [])
            print(f"{market.ticker}: {yes_levels} yes levels, {no_levels} no levels")


if __name__ == "__main__":
    # Choose which example to run:
    asyncio.run(browse_markets())
    # asyncio.run(stream_prices())
    # asyncio.run(parallel_requests())
