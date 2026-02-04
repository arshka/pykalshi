"""Tests for DataFrame conversion functionality."""

import pytest

from pykalshi.models import (
    PositionModel,
    FillModel,
    MarketModel,
    CandlestickResponse,
    Candlestick,
    PriceData,
    OrderbookResponse,
    Orderbook,
)
from pykalshi.enums import Side, Action

# Skip all tests if pandas is not installed
pd = pytest.importorskip("pandas")


class TestToDataFrame:
    """Tests for the to_dataframe function."""

    def test_import_from_package(self):
        """Can import to_dataframe and DataFrameList from main package."""
        from pykalshi import to_dataframe, DataFrameList
        assert callable(to_dataframe)
        assert DataFrameList is not None

    def test_import_from_module(self):
        """Can import to_dataframe from dataframe module."""
        from pykalshi.dataframe import to_dataframe, DataFrameList
        assert callable(to_dataframe)
        assert DataFrameList is not None

    def test_empty_list(self):
        """Empty list returns empty DataFrame."""
        from pykalshi import to_dataframe
        df = to_dataframe([])
        assert len(df) == 0

    def test_position_models(self):
        """Convert list of PositionModel to DataFrame."""
        from pykalshi import to_dataframe

        positions = [
            PositionModel(ticker="AAPL-YES", position=10, market_exposure=500),
            PositionModel(ticker="GOOG-NO", position=-5, market_exposure=250),
        ]

        df = to_dataframe(positions)

        assert len(df) == 2
        assert list(df["ticker"]) == ["AAPL-YES", "GOOG-NO"]
        assert list(df["position"]) == [10, -5]
        assert list(df["market_exposure"]) == [500, 250]

    def test_fill_models(self):
        """Convert list of FillModel to DataFrame."""
        from pykalshi import to_dataframe

        fills = [
            FillModel(
                trade_id="t1",
                ticker="BTC-50K",
                order_id="o1",
                side=Side.YES,
                action=Action.BUY,
                count=5,
                yes_price=45,
                no_price=55,
            ),
        ]

        df = to_dataframe(fills)

        assert len(df) == 1
        assert df.iloc[0]["ticker"] == "BTC-50K"
        assert df.iloc[0]["count"] == 5
        assert df.iloc[0]["yes_price"] == 45

    def test_market_models(self):
        """Convert list of MarketModel to DataFrame."""
        from pykalshi import to_dataframe

        markets = [
            MarketModel(ticker="KXBTC-24", title="BTC > 50K", yes_bid=45, yes_ask=47),
            MarketModel(ticker="KXETH-24", title="ETH > 3K", yes_bid=60, yes_ask=62),
        ]

        df = to_dataframe(markets)

        assert len(df) == 2
        assert "ticker" in df.columns
        assert "title" in df.columns
        assert "yes_bid" in df.columns

    def test_candlestick_response(self):
        """Convert CandlestickResponse to DataFrame with flattened price data."""
        from pykalshi import to_dataframe

        response = CandlestickResponse(
            ticker="BTC-50K",
            candlesticks=[
                Candlestick(
                    end_period_ts=1700000000,
                    volume=100,
                    open_interest=500,
                    price=PriceData(open=45, high=48, low=44, close=47),
                ),
                Candlestick(
                    end_period_ts=1700003600,
                    volume=150,
                    open_interest=520,
                    price=PriceData(open=47, high=50, low=46, close=49),
                ),
            ],
        )

        df = to_dataframe(response)

        assert len(df) == 2
        assert "ticker" in df.columns
        assert "timestamp" in df.columns
        assert "open" in df.columns
        assert "high" in df.columns
        assert "low" in df.columns
        assert "close" in df.columns
        assert df.iloc[0]["open"] == 45
        assert df.iloc[1]["close"] == 49

    def test_candlestick_response_method(self):
        """CandlestickResponse has .to_dataframe() method."""
        response = CandlestickResponse(
            ticker="BTC-50K",
            candlesticks=[
                Candlestick(
                    end_period_ts=1700000000,
                    volume=100,
                    open_interest=500,
                    price=PriceData(open=45, high=48, low=44, close=47),
                ),
            ],
        )

        df = response.to_dataframe()

        assert len(df) == 1
        assert df.iloc[0]["ticker"] == "BTC-50K"

    def test_single_model(self):
        """Single model returns single-row DataFrame."""
        from pykalshi import to_dataframe

        position = PositionModel(ticker="TEST", position=10)
        df = to_dataframe(position)

        assert len(df) == 1
        assert df.iloc[0]["ticker"] == "TEST"

    def test_dict_list(self):
        """Convert list of dicts to DataFrame."""
        from pykalshi import to_dataframe

        data = [
            {"ticker": "A", "value": 1},
            {"ticker": "B", "value": 2},
        ]

        df = to_dataframe(data)

        assert len(df) == 2
        assert list(df["ticker"]) == ["A", "B"]

    def test_orderbook_response(self):
        """Convert OrderbookResponse to DataFrame with price levels."""
        from pykalshi import to_dataframe

        response = OrderbookResponse(
            orderbook=Orderbook(
                yes=[(45, 100), (44, 50), (43, 25)],
                no=[(55, 75), (56, 30)],
            )
        )

        df = to_dataframe(response)

        assert len(df) == 5
        assert set(df["side"]) == {"yes", "no"}
        assert "price" in df.columns
        assert "quantity" in df.columns

    def test_orderbook_response_method(self):
        """OrderbookResponse has .to_dataframe() method."""
        response = OrderbookResponse(
            orderbook=Orderbook(
                yes=[(45, 100)],
                no=[(55, 75)],
            )
        )

        df = response.to_dataframe()

        assert len(df) == 2


class TestDataFrameList:
    """Tests for the DataFrameList class."""

    def test_is_list_subclass(self):
        """DataFrameList is a proper list subclass."""
        from pykalshi import DataFrameList

        dl = DataFrameList([1, 2, 3])
        assert isinstance(dl, list)
        assert len(dl) == 3
        assert dl[0] == 1

    def test_list_operations(self):
        """DataFrameList supports all list operations."""
        from pykalshi import DataFrameList

        dl = DataFrameList([1, 2])
        dl.append(3)
        assert len(dl) == 3

        dl.extend([4, 5])
        assert len(dl) == 5

        assert dl[2:4] == [3, 4]

    def test_slice_preserves_type(self):
        """Slicing a DataFrameList returns a DataFrameList."""
        from pykalshi import DataFrameList

        dl = DataFrameList([1, 2, 3, 4, 5])

        sliced = dl[1:4]
        assert isinstance(sliced, DataFrameList)
        assert sliced == [2, 3, 4]

        # Single index returns element, not DataFrameList
        assert dl[0] == 1
        assert not isinstance(dl[0], DataFrameList)

    def test_to_dataframe_method(self):
        """DataFrameList has .to_dataframe() method."""
        from pykalshi import DataFrameList

        positions = DataFrameList([
            PositionModel(ticker="A", position=10),
            PositionModel(ticker="B", position=-5),
        ])

        df = positions.to_dataframe()

        assert len(df) == 2
        assert list(df["ticker"]) == ["A", "B"]

    def test_repr(self):
        """DataFrameList has informative repr."""
        from pykalshi import DataFrameList

        dl = DataFrameList([1, 2, 3])
        assert "DataFrameList" in repr(dl)
        assert "[1, 2, 3]" in repr(dl)


class TestPandasNotInstalled:
    """Test behavior when pandas is not installed."""

    def test_helpful_error_message(self, monkeypatch):
        """Shows helpful error when pandas not installed."""
        import sys
        import builtins

        # Temporarily make pandas import fail
        real_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "pandas":
                raise ImportError("No module named 'pandas'")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)

        # Clear any cached pandas import
        if "pandas" in sys.modules:
            monkeypatch.delitem(sys.modules, "pandas")

        from pykalshi.dataframe import _import_pandas

        with pytest.raises(ImportError) as exc_info:
            _import_pandas()

        assert "pip install pykalshi[dataframe]" in str(exc_info.value)
