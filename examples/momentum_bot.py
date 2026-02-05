"""Simple momentum trading bot example.

A basic bot that tracks price movements and trades when momentum is detected.
This is for EDUCATIONAL PURPOSES - not financial advice.

Strategy:
    - Track the last N price updates for a market
    - If price moves consistently in one direction, enter a position
    - Exit when momentum reverses or profit target is hit

Setup:
    1. Create a .env file with your credentials
    2. Run: python examples/momentum_bot.py

WARNING: This bot places REAL orders when not in demo mode.
         Always test with demo=True first.
"""

import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime

from pykalshi import (
    KalshiClient,
    Feed,
    TickerMessage,
    Action,
    Side,
    OrderType,
    MarketStatus,
    InsufficientFundsError,
)


@dataclass
class BotConfig:
    """Bot configuration parameters."""
    ticker: str                    # Market to trade
    lookback: int = 5              # Number of price updates to track
    momentum_threshold: int = 3    # Consecutive moves to trigger entry
    position_size: int = 10        # Contracts per trade
    profit_target: int = 5         # Exit after N cents profit
    stop_loss: int = 3             # Exit after N cents loss
    max_position: int = 50         # Maximum contracts to hold
    demo: bool = True              # Use demo environment


class MomentumBot:
    """Simple momentum-following trading bot."""

    def __init__(self, config: BotConfig):
        self.config = config
        self.client = KalshiClient.from_env(demo=config.demo)
        self.portfolio = self.client.portfolio

        # Price tracking
        self.prices: deque[int] = deque(maxlen=config.lookback)
        self.last_price: int | None = None

        # Position tracking
        self.position: int = 0          # Positive = long YES, negative = long NO
        self.entry_price: int | None = None

        # Stats
        self.trades: int = 0
        self.pnl: int = 0  # In cents

    def log(self, msg: str):
        """Print timestamped log message."""
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] {msg}")

    def on_price_update(self, price: int):
        """Process a new price update."""
        if self.last_price is not None:
            # Track price direction: +1 = up, -1 = down, 0 = unchanged
            direction = 0
            if price > self.last_price:
                direction = 1
            elif price < self.last_price:
                direction = -1
            self.prices.append(direction)

        self.last_price = price

        # Check for signals
        if self.position == 0:
            self.check_entry_signal(price)
        else:
            self.check_exit_signal(price)

    def check_entry_signal(self, current_price: int):
        """Check if we should enter a position."""
        if len(self.prices) < self.config.momentum_threshold:
            return

        recent = list(self.prices)[-self.config.momentum_threshold:]

        # All recent moves in same direction = momentum
        if all(d == 1 for d in recent):
            self.enter_position(Side.YES, current_price)
        elif all(d == -1 for d in recent):
            self.enter_position(Side.NO, current_price)

    def check_exit_signal(self, current_price: int):
        """Check if we should exit the position."""
        if self.entry_price is None:
            return

        if self.position > 0:  # Long YES
            pnl = current_price - self.entry_price
        else:  # Long NO
            pnl = self.entry_price - current_price

        # Exit on profit target or stop loss
        if pnl >= self.config.profit_target:
            self.log(f"Profit target hit: +{pnl}¢")
            self.exit_position(current_price)
        elif pnl <= -self.config.stop_loss:
            self.log(f"Stop loss hit: {pnl}¢")
            self.exit_position(current_price)

        # Exit on momentum reversal
        if len(self.prices) >= 2:
            recent = list(self.prices)[-2:]
            if self.position > 0 and all(d == -1 for d in recent):
                self.log("Momentum reversal detected")
                self.exit_position(current_price)
            elif self.position < 0 and all(d == 1 for d in recent):
                self.log("Momentum reversal detected")
                self.exit_position(current_price)

    def enter_position(self, side: Side, price: int):
        """Enter a new position."""
        if abs(self.position) >= self.config.max_position:
            self.log(f"Max position reached ({self.config.max_position}), skipping entry")
            return

        # NOTE: Order placement commented out for testing
        # try:
        #     order = self.portfolio.place_order(
        #         self.config.ticker,
        #         action=Action.BUY,
        #         side=side,
        #         count=self.config.position_size,
        #         order_type=OrderType.MARKET,
        #     )
        # except InsufficientFundsError:
        #     self.log("Insufficient funds for entry")
        #     return
        # except Exception as e:
        #     self.log(f"Entry failed: {e}")
        #     return

        self.position = self.config.position_size if side == Side.YES else -self.config.position_size
        self.entry_price = price
        self.trades += 1

        self.log(f"ENTRY: {side.value} {self.config.position_size}x @ ~{price}¢ [SIMULATED]")

    def exit_position(self, price: int):
        """Exit current position."""
        if self.position == 0:
            return

        # To exit: sell what we bought
        if self.position > 0:
            side = Side.YES
            count = self.position
        else:
            side = Side.NO
            count = abs(self.position)

        # NOTE: Order placement commented out for testing
        # try:
        #     order = self.portfolio.place_order(
        #         self.config.ticker,
        #         action=Action.SELL,
        #         side=side,
        #         count=count,
        #         order_type=OrderType.MARKET,
        #     )
        # except Exception as e:
        #     self.log(f"Exit failed: {e}")
        #     return

        # Calculate P&L
        if self.entry_price:
            if self.position > 0:
                trade_pnl = (price - self.entry_price) * count
            else:
                trade_pnl = (self.entry_price - price) * count
            self.pnl += trade_pnl
            self.log(f"EXIT: {side.value} {count}x @ ~{price}¢ (P&L: {trade_pnl:+}¢, Total: {self.pnl:+}¢) [SIMULATED]")

        self.position = 0
        self.entry_price = None

    def handle_ticker(self, msg: TickerMessage):
        """Handle incoming ticker message."""
        if msg.price is not None:
            self.on_price_update(msg.price)

            # Status line
            pos_str = f"POS: {self.position:+}" if self.position else "POS: flat"
            print(f"  Price: {msg.price}¢ | {pos_str} | Trades: {self.trades} | P&L: {self.pnl:+}¢", end="\r")

    def run(self):
        """Main bot loop - stream prices and trade."""
        env = "DEMO" if self.config.demo else "LIVE"
        self.log(f"Starting momentum bot [{env}]")
        self.log(f"Market: {self.config.ticker}")
        self.log(f"Config: lookback={self.config.lookback}, threshold={self.config.momentum_threshold}")
        self.log(f"Risk: size={self.config.position_size}, target=+{self.config.profit_target}¢, stop=-{self.config.stop_loss}¢")
        self.log("-" * 50)

        # Check initial balance
        balance = self.portfolio.get_balance()
        self.log(f"Balance: ${balance.balance / 100:.2f}")

        with Feed(self.client) as feed:
            # Register handler
            feed.on("ticker", self.handle_ticker)

            # Subscribe to market
            feed.subscribe("ticker", market_ticker=self.config.ticker)
            self.log(f"Subscribed to {self.config.ticker}")
            self.log("Waiting for price updates...\n")

            # Run until interrupted
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print(f"\n\nBot stopped. Total P&L: {self.pnl:+}¢ over {self.trades} trades")


def main():
    # Find an active market to trade
    client = KalshiClient.from_env(demo=True)
    markets = client.get_markets(status=MarketStatus.OPEN, limit=10)

    if not markets:
        print("No open markets found")
        return

    # Pick a market with decent volume
    market = max(markets, key=lambda m: m.volume or 0)
    print(f"Selected market: {market.ticker}")
    print(f"  {market.title}")
    print(f"  Volume: {market.volume}, Price: {market.yes_bid}-{market.yes_ask}¢\n")

    config = BotConfig(
        ticker=market.ticker,
        lookback=5,
        momentum_threshold=3,
        position_size=10,
        profit_target=5,
        stop_loss=3,
        demo=True,  # ALWAYS test in demo first!
    )

    bot = MomentumBot(config)
    bot.run()


if __name__ == "__main__":
    main()
