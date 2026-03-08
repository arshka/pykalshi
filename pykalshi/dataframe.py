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
    """
    pd = _import_pandas()

    from .models import CandlestickResponse, OrderbookResponse

    if isinstance(obj, CandlestickResponse):
        return _candlesticks_to_df(obj, pd)

    if isinstance(obj, OrderbookResponse):
        return _orderbook_to_df(obj, pd)

    if isinstance(obj, Sequence) and not isinstance(obj, (str, bytes)):
        if len(obj) == 0:
            return pd.DataFrame()
        return _sequence_to_df(obj, pd)

    return _single_to_df(obj, pd)


def _single_to_df(obj: Any, pd) -> pd.DataFrame:
    data = _extract_data(obj)
    return pd.DataFrame([data])


def _sequence_to_df(items: Sequence, pd) -> pd.DataFrame:
    records = [_extract_data(item) for item in items]
    return pd.DataFrame(records)


def _extract_data(obj: Any) -> dict:
    """Extract a flat dict from an object.

    Uses mode='json' to serialize enums as their string values.
    """
    if hasattr(obj, 'data') and hasattr(obj.data, 'model_dump'):
        return obj.data.model_dump(mode='json')

    if hasattr(obj, 'model_dump'):
        return obj.model_dump(mode='json')

    if isinstance(obj, dict):
        return obj

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
            'volume_fp': candle.volume_fp,
            'open_interest_fp': candle.open_interest_fp,
        }

        if candle.price:
            for field in ('open_dollars', 'high_dollars', 'low_dollars', 'close_dollars', 'mean_dollars'):
                value = getattr(candle.price, field, None)
                if value is not None:
                    record[field] = value

        records.append(record)

    df = pd.DataFrame(records)

    if 'end_period_ts' in df.columns and len(df) > 0:
        df['timestamp'] = pd.to_datetime(df['end_period_ts'], unit='s')

    return df


def _orderbook_to_df(response: Any, pd) -> pd.DataFrame:
    """Convert OrderbookResponse to DataFrame with price levels.

    Returns DataFrame with columns: side, price_dollars, quantity_fp
    Sorted by price descending within each side.
    """
    from decimal import Decimal
    records = []

    if response.orderbook.yes_dollars:
        for price, quantity in response.orderbook.yes_dollars:
            records.append({'side': 'yes', 'price_dollars': price, 'quantity_fp': quantity})

    if response.orderbook.no_dollars:
        for price, quantity in response.orderbook.no_dollars:
            records.append({'side': 'no', 'price_dollars': price, 'quantity_fp': quantity})

    df = pd.DataFrame(records)

    if len(df) > 0:
        df['_sort_price'] = df['price_dollars'].apply(lambda x: float(Decimal(x)))
        df = df.sort_values(
            ['side', '_sort_price'],
            ascending=[False, False]
        ).drop(columns=['_sort_price']).reset_index(drop=True)

    return df
