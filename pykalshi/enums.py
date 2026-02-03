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


class MarketStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    SETTLED = "settled"
    ACTIVE = "active"
    FINALIZED = "finalized"


class CandlestickPeriod(int, Enum):
    """Candlestick period intervals in minutes."""

    ONE_MINUTE = 1
    ONE_HOUR = 60
    ONE_DAY = 1440


class TimeInForce(str, Enum):
    """Order time-in-force options."""

    GTC = "gtc"  # Good till canceled (default)
    IOC = "ioc"  # Immediate or cancel - fill what you can, cancel rest
    FOK = "fok"  # Fill or kill - fill entirely or cancel entirely


class SelfTradePrevention(str, Enum):
    """Self-trade prevention behavior."""

    CANCEL_TAKER = "cancel_resting"  # Cancel resting order on self-cross
    CANCEL_MAKER = "cancel_aggressing"  # Cancel incoming order on self-cross
