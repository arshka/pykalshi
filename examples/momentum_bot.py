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
from decimal import Decimal

from pykalshi import (
    KalshiClient,
    Feed,
    TickerMessage,
    Action,
    Side,
    MarketStatus,
    InsufficientFundsError,
)


@dataclass
class BotConfig:
    """Bot configuration parameters."""
    ticker: str                            # Market to trade
    lookback: int = 5                      # Number of price updates to track
    momentum_threshold: int = 3            # Consecutive moves to trigger entry
    position_size: str = "10.00"           # Contracts per trade (fp string)
    profit_target: str = "0.05"            # Exit after $0.05 profit
    stop_loss: str = "0.03"                # Exit after $0.03 loss
    max_position: str = "50.00"            # Maximum contracts to hold
    demo: bool = True                      # Use demo environment


class MomentumBot:
    """Simple momentum-following trading bot."""

    def __init__(self, config: BotConfig):
        self.config = config
        self.client = KalshiClient.from_env(demo=config.demo)
        self.portfolio = self.client.portfolio

        # Price tracking
        self.prices: deque[int] = deque(maxlen=config.lookback)
        self.last_price: Decimal | None = None

        # Position tracking
        self.position: Decimal = Decimal(0)  # Positive = long YES, negative = long NO
        self.entry_price: Decimal | None = None

        # Stats
        self.trades: int = 0
        self.pnl: Decimal = Decimal(0)

    def log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] {msg}")

    def on_price_update(self, price: Decimal):
        if self.last_price is not None:
            direction = 0
            if price > self.last_price:
                direction = 1
            elif price < self.last_price:
                direction = -1
            self.prices.append(direction)

        self.last_price = price

        if self.position == 0:
            self.check_entry_signal(price)
        else:
            self.check_exit_signal(price)

    def check_entry_signal(self, current_price: Decimal):
        if len(self.prices) < self.config.momentum_threshold:
            return

        recent = list(self.prices)[-self.config.momentum_threshold:]

        if all(d == 1 for d in recent):
            self.enter_position(Side.YES, current_price)
        elif all(d == -1 for d in recent):
            self.enter_position(Side.NO, current_price)

    def check_exit_signal(self, current_price: Decimal):
        if self.entry_price is None:
            return

        if self.position > 0:
            pnl = current_price - self.entry_price
        else:
            pnl = self.entry_price - current_price

        profit_target = Decimal(self.config.profit_target)
        stop_loss = Decimal(self.config.stop_loss)

        if pnl >= profit_target:
            self.log(f"Profit target hit: +${pnl}")
            self.exit_position(current_price)
        elif pnl <= -stop_loss:
            self.log(f"Stop loss hit: -${abs(pnl)}")
            self.exit_position(current_price)

        if len(self.prices) >= 2:
            recent = list(self.prices)[-2:]
            if self.position > 0 and all(d == -1 for d in recent):
                self.log("Momentum reversal detected")
                self.exit_position(current_price)
            elif self.position < 0 and all(d == 1 for d in recent):
                self.log("Momentum reversal detected")
                self.exit_position(current_price)

    def enter_position(self, side: Side, price: Decimal):
        if abs(self.position) >= Decimal(self.config.max_position):
            self.log(f"Max position reached ({self.config.max_position}), skipping entry")
            return

        size = Decimal(self.config.position_size)
        self.position = size if side == Side.YES else -size
        self.entry_price = price
        self.trades += 1

        self.log(f"ENTRY: {side.value} {self.config.position_size}x @ ~${price} [SIMULATED]")

    def exit_position(self, price: Decimal):
        if self.position == 0:
            return

        if self.position > 0:
            side = Side.YES
            count = self.position
        else:
            side = Side.NO
            count = abs(self.position)

        if self.entry_price:
            if self.position > 0:
                trade_pnl = (price - self.entry_price) * count
            else:
                trade_pnl = (self.entry_price - price) * count
            self.pnl += trade_pnl
            self.log(f"EXIT: {side.value} {count}x @ ~${price} (P&L: ${trade_pnl}, Total: ${self.pnl}) [SIMULATED]")

        self.position = Decimal(0)
        self.entry_price = None

    def handle_ticker(self, msg: TickerMessage):
        if msg.price_dollars is not None:
            price = Decimal(msg.price_dollars)
            self.on_price_update(price)

            pos_str = f"POS: {self.position:+}" if self.position else "POS: flat"
            print(f"  Price: ${msg.price_dollars} | {pos_str} | Trades: {self.trades} | P&L: ${self.pnl}", end="\r")

    def run(self):
        env = "DEMO" if self.config.demo else "LIVE"
        self.log(f"Starting momentum bot [{env}]")
        self.log(f"Market: {self.config.ticker}")
        self.log(f"Config: lookback={self.config.lookback}, threshold={self.config.momentum_threshold}")
        self.log(f"Risk: size={self.config.position_size}, target=+${self.config.profit_target}, stop=-${self.config.stop_loss}")
        self.log("-" * 50)

        balance = self.portfolio.get_balance()
        self.log(f"Balance: ${balance.balance / 100:.2f}")

        with Feed(self.client) as feed:
            feed.on("ticker", self.handle_ticker)
            feed.subscribe("ticker", market_ticker=self.config.ticker)
            self.log(f"Subscribed to {self.config.ticker}")
            self.log("Waiting for price updates...\n")

            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print(f"\n\nBot stopped. Total P&L: ${self.pnl} over {self.trades} trades")


def main():
    client = KalshiClient.from_env(demo=True)
    markets = client.get_markets(status=MarketStatus.OPEN, limit=10)

    if not markets:
        print("No open markets found")
        return

    market = max(markets, key=lambda m: Decimal(m.volume_fp or "0"))
    print(f"Selected market: {market.ticker}")
    print(f"  {market.title}")
    print(f"  Volume: {market.volume_fp}, Price: ${market.yes_bid_dollars}-${market.yes_ask_dollars}\n")

    config = BotConfig(
        ticker=market.ticker,
        lookback=5,
        momentum_threshold=3,
        position_size="10.00",
        profit_target="0.05",
        stop_loss="0.03",
        demo=True,
    )

    bot = MomentumBot(config)
    bot.run()


if __name__ == "__main__":
    main()
