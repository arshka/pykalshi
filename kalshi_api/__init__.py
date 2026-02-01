"""
Kalshi API Client Library

A clean, modular interface for the Kalshi trading API.
"""

import logging

from .client import KalshiClient
from .events import Event
from .markets import Market
from .orders import Order
from .portfolio import Portfolio
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
)
from .exceptions import (
    KalshiError,
    KalshiAPIError,
    AuthenticationError,
    InsufficientFundsError,
    ResourceNotFoundError,
)

# Set up logging to NullHandler by default to avoid "No handler found" warnings.
logging.getLogger(__name__).addHandler(logging.NullHandler())

__all__ = [
    # Client
    "KalshiClient",
    # Domain objects
    "Event",
    "Market",
    "Order",
    "Portfolio",
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
    # Exceptions
    "KalshiError",
    "KalshiAPIError",
    "AuthenticationError",
    "InsufficientFundsError",
    "ResourceNotFoundError",
]
