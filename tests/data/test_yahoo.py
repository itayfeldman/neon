from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from neon.lib.data.base import DataFetchError
from neon.lib.data.yahoo import YahooFinanceAdapter
from neon.lib.instruments.options.option_inputs import OptionInputs
from neon.lib.instruments.options.option_type import OptionType


def _make_ohlcv(close: float = 150.0) -> pd.DataFrame:
    return pd.DataFrame({
        "date": [pd.Timestamp("2026-05-01"), pd.Timestamp("2026-05-02")],
        "open": [149.0, 150.0],
        "high": [151.0, 152.0],
        "low": [148.0, 149.0],
        "close": [150.0, close],
        "volume": [1_000_000, 1_100_000],
    })


class TestFetch:
    def test_returns_ohlcv_dataframe(self):
        adapter = YahooFinanceAdapter()
        raw = pd.DataFrame({
            "Open": [149.0], "High": [151.0], "Low": [148.0],
            "Close": [150.0], "Volume": [1_000_000],
        }, index=pd.DatetimeIndex([pd.Timestamp("2026-05-01")], name="Date"))
        with patch("yfinance.download", return_value=raw):
            df = adapter.fetch("AAPL", use_cache=False)
        assert "close" in df.columns
        assert "date" in df.columns

    def test_raises_on_empty_response(self):
        adapter = YahooFinanceAdapter()
        with patch("yfinance.download", return_value=pd.DataFrame()):
            with pytest.raises(DataFetchError):
                adapter.fetch("INVALID", use_cache=False)

    def test_raises_on_network_failure(self):
        adapter = YahooFinanceAdapter()
        with patch("yfinance.download", side_effect=OSError("timeout")):
            with pytest.raises(DataFetchError):
                adapter.fetch("AAPL", use_cache=False)


class TestToDomain:
    def test_returns_dataframe_unchanged(self, alpha_vantage_df):
        adapter = YahooFinanceAdapter()
        df = _make_ohlcv()
        assert adapter.to_domain(df) is df


class TestSpot:
    def test_returns_most_recent_close(self):
        adapter = YahooFinanceAdapter()
        df = _make_ohlcv(close=182.0)
        with patch.object(adapter, "fetch", return_value=df):
            assert adapter.spot("AAPL") == pytest.approx(182.0)


class TestOptionChain:
    def test_returns_list_of_option_inputs(self):
        adapter = YahooFinanceAdapter()
        calls = pd.DataFrame({
            "strike": [150.0, 155.0],
            "impliedVolatility": [0.25, 0.27],
        })
        puts = pd.DataFrame({
            "strike": [145.0, 150.0],
            "impliedVolatility": [0.24, 0.26],
        })
        mock_chain = MagicMock()
        mock_chain.calls = calls
        mock_chain.puts = puts

        with patch.object(adapter, "spot", return_value=150.0):
            with patch("yfinance.Ticker") as mock_ticker:
                mock_ticker.return_value.option_chain.return_value = mock_chain
                result = adapter.option_chain("AAPL", "2026-06-20")

        assert len(result) == 4
        assert all(isinstance(r, OptionInputs) for r in result)
        calls_out = [r for r in result if r.option_type == OptionType.Call]
        puts_out = [r for r in result if r.option_type == OptionType.Put]
        assert len(calls_out) == 2
        assert len(puts_out) == 2

    def test_option_inputs_have_correct_expiry(self):
        adapter = YahooFinanceAdapter()
        calls = pd.DataFrame({"strike": [150.0], "impliedVolatility": [0.25]})
        puts = pd.DataFrame({"strike": [150.0], "impliedVolatility": [0.25]})
        mock_chain = MagicMock()
        mock_chain.calls = calls
        mock_chain.puts = puts

        with patch.object(adapter, "spot", return_value=150.0):
            with patch("yfinance.Ticker") as mock_ticker:
                mock_ticker.return_value.option_chain.return_value = mock_chain
                result = adapter.option_chain("AAPL", "2026-06-20")

        assert all(r.expiry_date == "20260620" for r in result)
