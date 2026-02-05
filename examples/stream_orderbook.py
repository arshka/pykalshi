"""WebSocket streaming example: real-time market data.

This example shows how to subscribe to live market updates via WebSocket.

Setup:
    1. Create a .env file with your credentials
    2. Run: python examples/stream_orderbook.py
"""

import time
from pykalshi import (
    KalshiClient,
    Feed,
    OrderbookManager,
    TickerMessage,
    TradeMessage,
    FillMessage,
    OrderbookSnapshotMessage,
    OrderbookDeltaMessage,
)

# Initialize client (loads credentials from .env)
client = KalshiClient.from_env()

# Replace with an active market ticker
TICKER = "INXD-25FEB03-B5975"


def stream_ticker():
    """Stream live ticker updates for a market."""
    print("Streaming ticker updates (Ctrl+C to stop)...\n")

    with Feed(client) as feed:
        @feed.on("ticker")
        def handle_ticker(msg: TickerMessage):
            print(f"[Ticker] {msg.market_ticker}: {msg.yes_bid}/{msg.yes_ask} (vol: {msg.volume})")

        feed.subscribe("ticker", market_ticker=TICKER)

        # Keep running until interrupted
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopped.")


def stream_orderbook():
    """Stream and maintain a local orderbook."""
    print("Streaming orderbook (Ctrl+C to stop)...\n")

    # OrderbookManager maintains local state from WebSocket updates
    books: dict[str, OrderbookManager] = {}

    with Feed(client) as feed:
        @feed.on("orderbook_delta")
        def handle_orderbook(msg):
            ticker = msg.market_ticker

            # Create manager for this ticker if needed
            if ticker not in books:
                books[ticker] = OrderbookManager(ticker)

            book = books[ticker]

            # Apply snapshot or delta
            if isinstance(msg, OrderbookSnapshotMessage):
                book.apply_snapshot(msg.yes, msg.no)
                print(f"[Snapshot] {ticker}: {len(book.yes)} yes levels, {len(book.no)} no levels")
            elif isinstance(msg, OrderbookDeltaMessage):
                book.apply_delta(msg.side, msg.price, msg.delta)
                print(f"[Delta] {ticker}: best_bid={book.best_bid}, best_ask={book.best_ask}, spread={book.spread}")

        feed.subscribe("orderbook_delta", market_ticker=TICKER)

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopped.")


def stream_trades():
    """Stream public trades."""
    print("Streaming trades (Ctrl+C to stop)...\n")

    with Feed(client) as feed:
        @feed.on("trade")
        def handle_trade(msg: TradeMessage):
            ticker = msg.market_ticker or msg.ticker
            print(f"[Trade] {ticker}: {msg.count}x @ {msg.yes_price}¢ ({msg.taker_side})")

        feed.subscribe("trade", market_ticker=TICKER)

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopped.")


def stream_multiple():
    """Subscribe to multiple data types at once."""
    print("Streaming multiple channels (Ctrl+C to stop)...\n")

    with Feed(client) as feed:
        @feed.on("ticker")
        def handle_ticker(msg: TickerMessage):
            print(f"[Ticker] {msg.market_ticker}: {msg.yes_bid}/{msg.yes_ask}")

        @feed.on("orderbook_delta")
        def handle_orderbook(msg):
            print(f"[Orderbook] {msg.market_ticker}: {type(msg).__name__}")

        @feed.on("trade")
        def handle_trade(msg: TradeMessage):
            ticker = msg.market_ticker or msg.ticker
            print(f"[Trade] {ticker}: {msg.count}x @ {msg.yes_price}¢")

        feed.subscribe("ticker", market_ticker=TICKER)
        feed.subscribe("orderbook_delta", market_ticker=TICKER)
        feed.subscribe("trade", market_ticker=TICKER)

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopped.")


def stream_portfolio():
    """Stream your own fills and position updates (private channel)."""
    print("Streaming portfolio updates (Ctrl+C to stop)...\n")

    with Feed(client) as feed:
        @feed.on("fill")
        def handle_fill(msg: FillMessage):
            print(f"[Fill] {msg.action} {msg.count}x {msg.ticker} @ {msg.yes_price}¢")

        # Subscribe to your fills (no market filter needed)
        feed.subscribe("fill")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopped.")


if __name__ == "__main__":
    # Choose which stream to run:
    stream_ticker()
    # stream_orderbook()
    # stream_trades()
    # stream_multiple()
    # stream_portfolio()
