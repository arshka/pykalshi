from enum import Enum


class Side(str, Enum):
    YES = "yes"
    NO = "no"


class Action(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    LIMIT = "limit"
    MARKET = "market"


class OrderStatus(str, Enum):
    RESTING = "resting"
    CANCELED = "canceled"
    FILLED = "filled"
    EXECUTED = "executed"


class CandlestickPeriod(int, Enum):
    """Candlestick period intervals in minutes."""

    ONE_MINUTE = 1
    ONE_HOUR = 60
    ONE_DAY = 1440
