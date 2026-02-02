"""Orderbook management utilities for maintaining local state."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class OrderbookManager:
    """Maintains local orderbook state from WebSocket updates.

    Usage with Feed:
        feed = client.feed()
        books = {}  # ticker -> OrderbookManager

        @feed.on("orderbook_delta")
        def handle_book(msg):
            ticker = msg.market_ticker
            if ticker not in books:
                books[ticker] = OrderbookManager(ticker)

            if hasattr(msg, 'yes'):  # Snapshot
                books[ticker].apply_snapshot(msg.yes, msg.no)
            else:  # Delta
                books[ticker].apply_delta(msg.side, msg.price, msg.delta)

            print(f"{ticker}: {books[ticker].spread}c spread")
    """

    ticker: str
    yes: dict[int, int] = field(default_factory=dict)  # price -> quantity
    no: dict[int, int] = field(default_factory=dict)

    def apply_snapshot(
        self,
        yes_levels: list[tuple[int, int]] | None,
        no_levels: list[tuple[int, int]] | None,
    ) -> None:
        """Reset book from snapshot message."""
        self.yes = {p: q for p, q in (yes_levels or [])}
        self.no = {p: q for p, q in (no_levels or [])}

    def apply_delta(self, side: str, price: int, delta: int) -> None:
        """Apply incremental update. Removes level if quantity hits zero."""
        book = self.yes if side == "yes" else self.no
        new_qty = book.get(price, 0) + delta
        if new_qty <= 0:
            book.pop(price, None)
        else:
            book[price] = new_qty

    @property
    def best_bid(self) -> Optional[int]:
        """Best YES bid price."""
        return max(self.yes.keys()) if self.yes else None

    @property
    def best_ask(self) -> Optional[int]:
        """Best YES ask (= 100 - best NO bid)."""
        if not self.no:
            return None
        return 100 - max(self.no.keys())

    @property
    def mid(self) -> Optional[float]:
        """Mid price."""
        if self.best_bid is None or self.best_ask is None:
            return None
        return (self.best_bid + self.best_ask) / 2

    @property
    def spread(self) -> Optional[int]:
        """Bid-ask spread in cents."""
        if self.best_bid is None or self.best_ask is None:
            return None
        return self.best_ask - self.best_bid

    def bid_depth(self, levels: int = 5) -> int:
        """Total quantity in top N bid levels."""
        if not self.yes:
            return 0
        sorted_prices = sorted(self.yes.keys(), reverse=True)[:levels]
        return sum(self.yes[p] for p in sorted_prices)

    def ask_depth(self, levels: int = 5) -> int:
        """Total quantity in top N ask levels."""
        if not self.no:
            return 0
        sorted_prices = sorted(self.no.keys(), reverse=True)[:levels]
        return sum(self.no[p] for p in sorted_prices)

    @property
    def imbalance(self) -> Optional[float]:
        """Order imbalance [-1, 1]. Positive = more bids."""
        bid_total = sum(self.yes.values()) if self.yes else 0
        ask_total = sum(self.no.values()) if self.no else 0
        total = bid_total + ask_total
        if total == 0:
            return None
        return (bid_total - ask_total) / total

    def cost_to_buy(self, size: int) -> Optional[tuple[int, float]]:
        """Calculate cost to buy `size` YES contracts.

        Returns:
            Tuple of (total_cost, avg_price) or None if insufficient liquidity.
        """
        if not self.no:
            return None

        remaining = size
        cost = 0
        for no_price in sorted(self.no.keys(), reverse=True):
            qty = self.no[no_price]
            take = min(remaining, qty)
            yes_price = 100 - no_price
            cost += take * yes_price
            remaining -= take
            if remaining <= 0:
                return (cost, cost / size)
        return None

    def cost_to_sell(self, size: int) -> Optional[tuple[int, float]]:
        """Calculate proceeds from selling `size` YES contracts.

        Returns:
            Tuple of (total_proceeds, avg_price) or None if insufficient liquidity.
        """
        if not self.yes:
            return None

        remaining = size
        proceeds = 0
        for price in sorted(self.yes.keys(), reverse=True):
            qty = self.yes[price]
            take = min(remaining, qty)
            proceeds += take * price
            remaining -= take
            if remaining <= 0:
                return (proceeds, proceeds / size)
        return None

    def __repr__(self) -> str:
        bid = self.best_bid or "—"
        ask = self.best_ask or "—"
        return f"<Orderbook {self.ticker} {bid}/{ask}>"
