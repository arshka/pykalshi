"""
Kalshi API Client Library

A clean, modular interface for the Kalshi trading API.
"""

import logging

from .client import KalshiClient
from .events import Event
from .markets import Market, Series
from .orders import Order
from .portfolio import Portfolio
from .exchange import Exchange
from .api_keys import APIKeys
from .feed import (
    Feed,
    TickerMessage,
    OrderbookSnapshotMessage,
    OrderbookDeltaMessage,
    OrderbookMessage,
    TradeMessage,
    FillMessage,
)
from .enums import (
    Side,
    Action,
    OrderType,
    OrderStatus,
    MarketStatus,
    CandlestickPeriod,
)
from .models import (
    PositionModel,
    FillModel,
    OrderModel,
    BalanceModel,
    MarketModel,
    EventModel,
    OrderbookResponse,
    CandlestickResponse,
    ExchangeStatus,
    ExchangeSchedule,
    Announcement,
    APILimits,
    APIKey,
    GeneratedAPIKey,
    SeriesModel,
    TradeModel,
)
from .exceptions import (
    KalshiError,
    KalshiAPIError,
    AuthenticationError,
    InsufficientFundsError,
    ResourceNotFoundError,
    RateLimitError,
)

# Set up logging to NullHandler by default to avoid "No handler found" warnings.
logging.getLogger(__name__).addHandler(logging.NullHandler())

__all__ = [
    # Client
    "KalshiClient",
    # Domain objects
    "Event",
    "Market",
    "Series",
    "Order",
    "Portfolio",
    "Exchange",
    "APIKeys",
    # Feed (WebSocket)
    "Feed",
    "TickerMessage",
    "OrderbookSnapshotMessage",
    "OrderbookDeltaMessage",
    "OrderbookMessage",
    "TradeMessage",
    "FillMessage",
    # Enums
    "Side",
    "Action",
    "OrderType",
    "OrderStatus",
    "MarketStatus",
    "CandlestickPeriod",
    # Models
    "PositionModel",
    "FillModel",
    "OrderModel",
    "BalanceModel",
    "MarketModel",
    "EventModel",
    "OrderbookResponse",
    "CandlestickResponse",
    "ExchangeStatus",
    "ExchangeSchedule",
    "Announcement",
    "APILimits",
    "APIKey",
    "GeneratedAPIKey",
    "SeriesModel",
    "TradeModel",
    # Exceptions
    "KalshiError",
    "KalshiAPIError",
    "AuthenticationError",
    "InsufficientFundsError",
    "ResourceNotFoundError",
    "RateLimitError",
]
