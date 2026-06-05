from unittest.mock import MagicMock, patch

import pytest

from neon.lib.data.alpha_vantage import AlphaVantageAdapter
from neon.lib.data.base import DataFetchError
from tests.data.conftest import ALPHA_VANTAGE_DAILY_JSON, ALPHA_VANTAGE_FX_JSON


class TestInit:
    def test_raises_without_api_key(self, monkeypatch):
        monkeypatch.delenv("ALPHA_VANTAGE_API_KEY", raising=False)
        with pytest.raises(ValueError):
            AlphaVantageAdapter()

    def test_accepts_explicit_api_key(self):
        adapter = AlphaVantageAdapter(api_key="test-key")
        assert adapter._api_key == "test-key"


class TestFetch:
    def test_returns_ohlcv_dataframe(self):
        adapter = AlphaVantageAdapter(api_key="test-key")
        mock_resp = MagicMock()
        mock_resp.read.return_value = ALPHA_VANTAGE_DAILY_JSON
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        with patch("urllib.request.urlopen", return_value=mock_resp):
            df = adapter.fetch("AAPL", use_cache=False)
        assert list(df.columns) == ["date", "open", "high", "low", "close", "volume"]
        assert len(df) == 2

    def test_sorted_ascending_by_date(self):
        adapter = AlphaVantageAdapter(api_key="test-key")
        mock_resp = MagicMock()
        mock_resp.read.return_value = ALPHA_VANTAGE_DAILY_JSON
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        with patch("urllib.request.urlopen", return_value=mock_resp):
            df = adapter.fetch("AAPL", use_cache=False)
        assert list(df["date"]) == sorted(df["date"])

    def test_raises_on_network_failure(self):
        adapter = AlphaVantageAdapter(api_key="test-key")
        with patch("urllib.request.urlopen", side_effect=OSError("timeout")):
            with pytest.raises(DataFetchError):
                adapter.fetch("AAPL", use_cache=False)

    def test_raises_on_unexpected_response(self):
        adapter = AlphaVantageAdapter(api_key="test-key")
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{"Note": "API rate limit reached"}'
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        with patch("urllib.request.urlopen", return_value=mock_resp):
            with pytest.raises(DataFetchError):
                adapter.fetch("AAPL", use_cache=False)


class TestToDomain:
    def test_returns_dataframe_unchanged(self, alpha_vantage_df):
        adapter = AlphaVantageAdapter(api_key="test-key")
        assert adapter.to_domain(alpha_vantage_df) is alpha_vantage_df


class TestFxRate:
    def test_returns_float(self):
        adapter = AlphaVantageAdapter(api_key="test-key")
        mock_resp = MagicMock()
        mock_resp.read.return_value = ALPHA_VANTAGE_FX_JSON
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        with patch("urllib.request.urlopen", return_value=mock_resp):
            rate = adapter.fx_rate("USD", "EUR", use_cache=False)
        assert isinstance(rate, float)
        assert rate == pytest.approx(0.925)

    def test_raises_on_unexpected_response(self):
        adapter = AlphaVantageAdapter(api_key="test-key")
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{"Note": "API rate limit reached"}'
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        with patch("urllib.request.urlopen", return_value=mock_resp):
            with pytest.raises(DataFetchError):
                adapter.fx_rate("USD", "EUR", use_cache=False)
