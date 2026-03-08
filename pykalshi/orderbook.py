"""Orderbook management utilities for maintaining local state."""

from __future__ import annotations
from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class OrderbookManager:
    """Maintains local orderbook state from WebSocket updates.

    All prices are dollar strings (e.g. "0.45") and quantities are
    fixed-point strings (e.g. "10.00").

    Usage with Feed:
        feed = client.feed()
        books = {}  # ticker -> OrderbookManager

        @feed.on("orderbook_delta")
        def handle_book(msg):
            ticker = msg.market_ticker
            if ticker not in books:
                books[ticker] = OrderbookManager(ticker)

            if hasattr(msg, 'yes_dollars'):  # Snapshot
                books[ticker].apply_snapshot(msg.yes_dollars, msg.no_dollars)
            else:  # Delta
                books[ticker].apply_delta(msg.side, msg.price_dollars, msg.delta_fp)

            print(f"{ticker}: ${books[ticker].spread} spread")
    """

    ticker: str
    yes: dict[str, str] = field(default_factory=dict)  # price_dollars -> quantity_fp
    no: dict[str, str] = field(default_factory=dict)

    def apply_snapshot(
        self,
        yes_levels: list[tuple[str, str]] | None,
        no_levels: list[tuple[str, str]] | None,
    ) -> None:
        """Reset book from snapshot message."""
        self.yes = {p: q for p, q in (yes_levels or [])}
        self.no = {p: q for p, q in (no_levels or [])}

    def apply_delta(self, side: str, price_dollars: str, delta_fp: str) -> None:
        """Apply incremental update. Removes level if quantity hits zero."""
        book = self.yes if side == "yes" else self.no
        new_qty = Decimal(book.get(price_dollars, "0")) + Decimal(delta_fp)
        if new_qty <= 0:
            book.pop(price_dollars, None)
        else:
            book[price_dollars] = str(new_qty)

    @property
    def best_bid(self) -> str | None:
        """Best YES bid price (dollar string)."""
        if not self.yes:
            return None
        return str(max(Decimal(p) for p in self.yes))

    @property
    def best_ask(self) -> str | None:
        """Best YES ask (= 1.00 - best NO bid), dollar string."""
        if not self.no:
            return None
        return str(Decimal("1") - max(Decimal(p) for p in self.no))

    @property
    def mid(self) -> str | None:
        """Mid price (dollar string)."""
        if self.best_bid is None or self.best_ask is None:
            return None
        return str((Decimal(self.best_bid) + Decimal(self.best_ask)) / 2)

    @property
    def spread(self) -> str | None:
        """Bid-ask spread (dollar string)."""
        if self.best_bid is None or self.best_ask is None:
            return None
        return str(Decimal(self.best_ask) - Decimal(self.best_bid))

    def bid_depth(self, levels: int = 5) -> str:
        """Total quantity in top N bid levels (fp string)."""
        if not self.yes:
            return "0"
        sorted_prices = sorted(self.yes.keys(), key=lambda p: Decimal(p), reverse=True)[:levels]
        return str(sum(Decimal(self.yes[p]) for p in sorted_prices))

    def ask_depth(self, levels: int = 5) -> str:
        """Total quantity in top N ask levels (fp string)."""
        if not self.no:
            return "0"
        sorted_prices = sorted(self.no.keys(), key=lambda p: Decimal(p), reverse=True)[:levels]
        return str(sum(Decimal(self.no[p]) for p in sorted_prices))

    @property
    def imbalance(self) -> float | None:
        """Order imbalance [-1, 1]. Positive = more bids."""
        bid_total = sum(Decimal(v) for v in self.yes.values()) if self.yes else Decimal(0)
        ask_total = sum(Decimal(v) for v in self.no.values()) if self.no else Decimal(0)
        total = bid_total + ask_total
        if total == 0:
            return None
        return float((bid_total - ask_total) / total)

    def cost_to_buy(self, size: str) -> tuple[str, str] | None:
        """Calculate cost to buy `size` YES contracts.

        Returns:
            Tuple of (total_cost_dollars, avg_price_dollars) or None if insufficient liquidity.
        """
        if not self.no:
            return None

        remaining = Decimal(size)
        cost = Decimal(0)
        for no_price_str in sorted(self.no.keys(), key=lambda p: Decimal(p), reverse=True):
            qty = Decimal(self.no[no_price_str])
            take = min(remaining, qty)
            yes_price = Decimal("1") - Decimal(no_price_str)
            cost += take * yes_price
            remaining -= take
            if remaining <= 0:
                return (str(cost), str(cost / Decimal(size)))
        return None

    def cost_to_sell(self, size: str) -> tuple[str, str] | None:
        """Calculate proceeds from selling `size` YES contracts.

        Returns:
            Tuple of (total_proceeds_dollars, avg_price_dollars) or None if insufficient liquidity.
        """
        if not self.yes:
            return None

        remaining = Decimal(size)
        proceeds = Decimal(0)
        for price_str in sorted(self.yes.keys(), key=lambda p: Decimal(p), reverse=True):
            qty = Decimal(self.yes[price_str])
            take = min(remaining, qty)
            proceeds += take * Decimal(price_str)
            remaining -= take
            if remaining <= 0:
                return (str(proceeds), str(proceeds / Decimal(size)))
        return None

    def __repr__(self) -> str:
        bid = self.best_bid or "—"
        ask = self.best_ask or "—"
        return f"<Orderbook {self.ticker} ${bid}/${ask}>"
