"""Basic usage example: browsing markets and checking your portfolio.

Setup:
    1. Create a .env file with your credentials:
       KALSHI_API_KEY_ID=your-key-id
       KALSHI_PRIVATE_KEY_PATH=/path/to/private-key.key

    2. Run: python examples/basic_usage.py
"""

from pykalshi import KalshiClient

# Initialize client (loads credentials from .env)
client = KalshiClient()

# For demo environment, use:
# client = KalshiClient(demo=True)

# --- Portfolio ---

user = client.get_user()

# Check balance (values in cents)
balance = user.get_balance()
print(f"Balance: ${balance.balance / 100:.2f}")
print(f"Portfolio value: ${balance.portfolio_value / 100:.2f}")

# View positions
positions = user.get_positions()
print(f"\nYou have {len(positions)} open positions")
for pos in positions[:5]:  # Show first 5
    print(f"  {pos.ticker}: {pos.position} contracts @ ${pos.market_exposure / 100:.2f} exposure")

# View recent fills
fills = user.get_fills(limit=5)
print(f"\nRecent fills:")
for fill in fills:
    print(f"  {fill.ticker}: {fill.action} {fill.count}x @ {fill.yes_price}¢")

# --- Markets ---

# Browse open markets
markets = client.get_markets(status="open", limit=10)
print(f"\n{len(markets)} open markets:")
for market in markets[:5]:
    print(f"  {market.ticker}: {market.title}")
    print(f"    Yes: {market.yes_bid}¢ bid / {market.yes_ask}¢ ask")

# Get a specific market
# market = client.get_market("KXBTC-25JAN15-B100000")
# print(f"\n{market.title}")
# print(f"  Status: {market.status}")
# print(f"  Volume: {market.volume} contracts")

# Get orderbook
if markets:
    market = markets[0]
    orderbook = market.get_orderbook()
    print(f"\nOrderbook for {market.ticker}:")
    print(f"  Yes bids: {len(orderbook.yes)} levels")
    print(f"  No bids: {len(orderbook.no)} levels")

# --- Events and Series ---

# Get events (groups of related markets)
events = client.get_events(status="open", limit=5)
print(f"\n{len(events)} open events:")
for event in events:
    print(f"  {event.event_ticker}: {event.title}")

# Get series (recurring event types)
series = client.get_series("KXBTC")  # Bitcoin price series
print(f"\nSeries: {series.title}")
print(f"  Category: {series.category}")
