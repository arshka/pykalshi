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
    OrderStatus,
    MarketStatus,
    InsufficientFundsError,
    OrderRejectedError,
)

# Use demo environment for testing (loads credentials from .env)
client = KalshiClient.from_env(demo=True)
portfolio = client.portfolio

# Check balance first
balance = portfolio.get_balance()
print(f"Available balance: ${balance.balance / 100:.2f}")

# --- Place a Limit Order ---

# Find a market to trade
markets = client.get_markets(status=MarketStatus.OPEN, limit=1)
if not markets:
    print("No open markets found")
    exit()

market = markets[0]
print(f"\nMarket: {market.ticker}")
print(f"  {market.title}")
print(f"  Current: ${market.yes_bid_dollars} bid / ${market.yes_ask_dollars} ask")

# Place a limit order (uncomment to execute)
# try:
#     order = portfolio.place_order(
#         market,
#         action=Action.BUY,
#         side=Side.YES,
#         count_fp="10.00",              # 10 contracts
#         yes_price_dollars="0.45",      # $0.45 per contract
#     )
#     print(f"\nOrder placed: {order.order_id}")
#     print(f"  Status: {order.status}")
#     print(f"  Remaining: {order.remaining_count_fp} contracts")
# except InsufficientFundsError:
#     print("Not enough balance")
# except OrderRejectedError as e:
#     print(f"Order rejected: {e.message}")


# --- View and Manage Orders ---

# Get your open orders
orders = portfolio.get_orders(status=OrderStatus.RESTING)
print(f"\nYou have {len(orders)} open orders")

for order in orders[:3]:
    print(f"  {order.order_id}: {order.action} {order.initial_count_fp}x {order.ticker} @ ${order.yes_price_dollars}")
    print(f"    Status: {order.status}, Filled: {order.fill_count_fp}")

# Cancel an order (uncomment to execute)
# if orders:
#     order = orders[0]
#     order.cancel()
#     print(f"Cancelled order {order.order_id}")

# Amend an order (uncomment to execute)
# if orders:
#     order = orders[0]
#     modified = order.amend(yes_price_dollars="0.50", count_fp="20.00")
#     print(f"Amended order: new price ${modified.yes_price_dollars}, new count {modified.initial_count_fp}")


# --- Sell / Close Position ---

# To close a YES position, sell YES contracts
# positions = portfolio.get_positions()
# for pos in positions:
#     from decimal import Decimal
#     if Decimal(pos.position_fp) > 0:  # Long YES position
#         order = portfolio.place_order(
#             pos.ticker,
#             action=Action.SELL,
#             side=Side.YES,
#             count_fp=pos.position_fp,
#             yes_price_dollars="0.01",  # Aggressive price to fill quickly
#         )
#         print(f"Closed position in {pos.ticker}")


# --- Advanced: Post-Only Orders ---

# Post-only orders are rejected if they would take liquidity.
# Essential for market making strategies to ensure you always earn the spread.

# order = portfolio.place_order(
#     market,
#     action=Action.BUY,
#     side=Side.YES,
#     count_fp="10.00",
#     yes_price_dollars=market.yes_bid_dollars,  # Bid at current best bid
#     post_only=True,                            # Reject if this would cross the spread
# )
