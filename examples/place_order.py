"""Trading example: placing and managing orders.

WARNING: This example places REAL orders. Use demo=True for testing,
or uncomment the actual order placement lines only when ready.

Setup:
    1. Create a .env file with your credentials
    2. Run: python examples/place_order.py
"""

from pykalshi import (
    KalshiClient,
    Action,
    Side,
    OrderType,
    InsufficientFundsError,
    OrderRejectedError,
)

# Use demo environment for testing
client = KalshiClient(demo=True)
user = client.get_user()

# Check balance first
balance = user.get_balance()
print(f"Available balance: ${balance.balance / 100:.2f}")

# --- Place a Limit Order ---

# Find a market to trade
markets = client.get_markets(status="open", limit=1)
if not markets:
    print("No open markets found")
    exit()

market = markets[0]
print(f"\nMarket: {market.ticker}")
print(f"  {market.title}")
print(f"  Current: {market.yes_bid}¢ bid / {market.yes_ask}¢ ask")

# Place a limit order (uncomment to execute)
# try:
#     order = user.place_order(
#         market,
#         action=Action.BUY,
#         side=Side.YES,
#         count=10,              # 10 contracts
#         yes_price=45,          # 45 cents per contract
#     )
#     print(f"\nOrder placed: {order.order_id}")
#     print(f"  Status: {order.status}")
#     print(f"  Remaining: {order.remaining_count} contracts")
# except InsufficientFundsError:
#     print("Not enough balance")
# except OrderRejectedError as e:
#     print(f"Order rejected: {e.message}")


# --- Place a Market Order ---

# Market orders execute immediately at best available price
# try:
#     order = user.place_order(
#         market,
#         action=Action.BUY,
#         side=Side.YES,
#         count=5,
#         order_type=OrderType.MARKET,
#     )
#     print(f"Market order filled: {order.order_id}")
# except InsufficientFundsError:
#     print("Not enough balance")


# --- View and Manage Orders ---

# Get your open orders
orders = user.get_orders(status="resting")
print(f"\nYou have {len(orders)} open orders")

for order in orders[:3]:
    print(f"  {order.order_id}: {order.action} {order.count}x {order.ticker} @ {order.yes_price}¢")
    print(f"    Status: {order.status}, Filled: {order.count - order.remaining_count}")

# Cancel an order (uncomment to execute)
# if orders:
#     order = orders[0]
#     order.cancel()
#     print(f"Cancelled order {order.order_id}")

# Modify an order (uncomment to execute)
# if orders:
#     order = orders[0]
#     modified = order.modify(yes_price=50, count=20)
#     print(f"Modified order: new price {modified.yes_price}¢, new count {modified.count}")


# --- Sell / Close Position ---

# To close a YES position, sell YES contracts
# positions = user.get_positions()
# for pos in positions:
#     if pos.position > 0:  # Long YES position
#         order = user.place_order(
#             pos.ticker,
#             action=Action.SELL,
#             side=Side.YES,
#             count=pos.position,
#             order_type=OrderType.MARKET,
#         )
#         print(f"Closed position in {pos.ticker}")


# --- Advanced: Post-Only Orders ---

# Post-only orders are rejected if they would take liquidity.
# Essential for market making strategies to ensure you always earn the spread.

# order = user.place_order(
#     market,
#     action=Action.BUY,
#     side=Side.YES,
#     count=10,
#     yes_price=market.yes_bid,  # Bid at current best bid
#     post_only=True,            # Reject if this would cross the spread
# )
