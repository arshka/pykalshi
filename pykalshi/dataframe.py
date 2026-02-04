"""Optional DataFrame conversion for pykalshi objects.

Requires pandas: pip install pykalshi[dataframe]

Usage:
    # Methods return DataFrameList - call .to_dataframe() directly:
    df = client.portfolio.get_positions().to_dataframe()
    df = client.portfolio.get_fills().to_dataframe()
    df = client.get_markets().to_dataframe()

    # Or use the standalone function:
    from pykalshi import to_dataframe
    df = to_dataframe(positions)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic, Sequence, SupportsIndex, TypeVar, overload

if TYPE_CHECKING:
    import pandas as pd

T = TypeVar('T')


class DataFrameList(list, Generic[T]):
    """A list subclass with DataFrame conversion support.

    Behaves exactly like a normal list, but adds a .to_dataframe() method
    for convenient conversion to pandas DataFrames.

    Example:
        positions = client.portfolio.get_positions()  # Returns DataFrameList
        df = positions.to_dataframe()
    """

    @overload
    def __getitem__(self, index: SupportsIndex) -> T: ...
    @overload
    def __getitem__(self, index: slice) -> DataFrameList[T]: ...

    def __getitem__(self, index):  # type: ignore[override]
        result = super().__getitem__(index)
        if isinstance(index, slice):
            return DataFrameList(result)
        return result

    def to_dataframe(self) -> pd.DataFrame:
        """Convert this list to a pandas DataFrame.

        Requires pandas: pip install pykalshi[dataframe]
        """
        return to_dataframe(self)

    def __repr__(self) -> str:
        return f"DataFrameList({super().__repr__()})"


def _import_pandas():
    """Lazy import pandas with helpful error message."""
    try:
        import pandas as pd
        return pd
    except ImportError:
        raise ImportError(
            "pandas is required for DataFrame conversion. "
            "Install it with: pip install pykalshi[dataframe]"
        ) from None


def to_dataframe(obj: Any) -> pd.DataFrame:
    """Convert a pykalshi object or list of objects to a pandas DataFrame.

    Supports:
        - Lists of Pydantic models (PositionModel, FillModel, etc.)
        - Lists of domain objects (Market, Order, Event, Series)
        - CandlestickResponse (extracts candlesticks with flattened price data)
        - Single Pydantic models (returns single-row DataFrame)

    Args:
        obj: A pykalshi object or list of objects.

    Returns:
        A pandas DataFrame with appropriate columns.

    Examples:
        >>> positions = client.portfolio.get_positions()
        >>> df = to_dataframe(positions)

        >>> markets = client.get_markets(limit=100)
        >>> df = to_dataframe(markets)

        >>> candles = market.get_candlesticks(start_ts, end_ts)
        >>> df = to_dataframe(candles)
    """
    pd = _import_pandas()

    # Import here to avoid circular imports
    from .models import CandlestickResponse, OrderbookResponse

    # Handle CandlestickResponse specially - flatten nested price data
    if isinstance(obj, CandlestickResponse):
        return _candlesticks_to_df(obj, pd)

    # Handle OrderbookResponse - convert to price level rows
    if isinstance(obj, OrderbookResponse):
        return _orderbook_to_df(obj, pd)

    # Handle sequences
    if isinstance(obj, Sequence) and not isinstance(obj, (str, bytes)):
        if len(obj) == 0:
            return pd.DataFrame()
        return _sequence_to_df(obj, pd)

    # Handle single objects
    return _single_to_df(obj, pd)


def _single_to_df(obj: Any, pd) -> pd.DataFrame:
    """Convert a single object to a single-row DataFrame."""
    data = _extract_data(obj)
    return pd.DataFrame([data])


def _sequence_to_df(items: Sequence, pd) -> pd.DataFrame:
    """Convert a sequence of objects to a DataFrame."""
    records = [_extract_data(item) for item in items]
    return pd.DataFrame(records)


def _extract_data(obj: Any) -> dict:
    """Extract a flat dict from an object.

    Handles:
        - Domain objects with .data attribute (Market, Order, Event, Series)
        - Pydantic models with .model_dump()
        - Plain dicts

    Uses mode='json' to serialize enums as their string values.
    """
    # Domain objects wrap a Pydantic model in .data
    if hasattr(obj, 'data') and hasattr(obj.data, 'model_dump'):
        return obj.data.model_dump(mode='json')

    # Pydantic models
    if hasattr(obj, 'model_dump'):
        return obj.model_dump(mode='json')

    # Already a dict
    if isinstance(obj, dict):
        return obj

    # Fallback: try __dict__
    if hasattr(obj, '__dict__'):
        return {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}

    raise TypeError(f"Cannot convert {type(obj).__name__} to DataFrame")


def _candlesticks_to_df(response: Any, pd) -> pd.DataFrame:
    """Convert CandlestickResponse to DataFrame with flattened price columns."""
    records = []
    for candle in response.candlesticks:
        record = {
            'ticker': response.ticker,
            'end_period_ts': candle.end_period_ts,
            'volume': candle.volume,
            'open_interest': candle.open_interest,
        }

        # Flatten price data
        if candle.price:
            for field in ('open', 'high', 'low', 'close', 'mean'):
                value = getattr(candle.price, field, None)
                if value is not None:
                    record[field] = value

        records.append(record)

    df = pd.DataFrame(records)

    # Convert timestamp to datetime if pandas available
    if 'end_period_ts' in df.columns and len(df) > 0:
        df['timestamp'] = pd.to_datetime(df['end_period_ts'], unit='s')

    return df


def _orderbook_to_df(response: Any, pd) -> pd.DataFrame:
    """Convert OrderbookResponse to DataFrame with price levels.

    Returns DataFrame with columns: side, price, quantity
    Sorted by price descending within each side.
    """
    records = []

    if response.orderbook.yes:
        for price, quantity in response.orderbook.yes:
            records.append({'side': 'yes', 'price': price, 'quantity': quantity})

    if response.orderbook.no:
        for price, quantity in response.orderbook.no:
            records.append({'side': 'no', 'price': price, 'quantity': quantity})

    df = pd.DataFrame(records)

    if len(df) > 0:
        # Sort: yes side first, then by price descending
        df = df.sort_values(
            ['side', 'price'],
            ascending=[False, False]
        ).reset_index(drop=True)

    return df
