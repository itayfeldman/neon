from unittest.mock import MagicMock, patch

import pytest

from neon.lib.data.base import DataFetchError
from neon.lib.data.fred import FREDAdapter
from neon.lib.fixed_income.discount_curve import DiscountCurve
from tests.data.conftest import FRED_SERIES_JSON


class TestInit:
    def test_raises_without_api_key(self, monkeypatch):
        monkeypatch.delenv("FRED_API_KEY", raising=False)
        with pytest.raises(ValueError):
            FREDAdapter()

    def test_accepts_explicit_api_key(self):
        adapter = FREDAdapter(api_key="test-key")
        assert adapter._api_key == "test-key"


class TestFetch:
    def test_returns_dataframe(self):
        adapter = FREDAdapter(api_key="test-key")
        mock_resp = MagicMock()
        mock_resp.read.return_value = FRED_SERIES_JSON
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        with patch("urllib.request.urlopen", return_value=mock_resp):
            df = adapter.fetch("DGS10", use_cache=False)
        assert list(df.columns) == ["date", "value"]
        assert len(df) == 3

    def test_raises_on_network_failure(self):
        adapter = FREDAdapter(api_key="test-key")
        with patch("urllib.request.urlopen", side_effect=OSError("timeout")):
            with pytest.raises(DataFetchError):
                adapter.fetch("DGS10", use_cache=False)


class TestToDomain:
    def test_returns_series(self, fred_series_df):
        adapter = FREDAdapter(api_key="test-key")
        series = adapter.to_domain(fred_series_df)
        assert series.name == "value"
        assert len(series) == 3


class TestYieldCurve:
    def test_returns_discount_curve(self):
        adapter = FREDAdapter(api_key="test-key")
        mock_resp = MagicMock()
        mock_resp.read.return_value = FRED_SERIES_JSON
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        with patch("urllib.request.urlopen", return_value=mock_resp):
            curve = adapter.yield_curve("20260501", use_cache=False)
        assert isinstance(curve, DiscountCurve)

    def test_discount_factors_are_valid(self):
        adapter = FREDAdapter(api_key="test-key")
        mock_resp = MagicMock()
        mock_resp.read.return_value = FRED_SERIES_JSON
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        with patch("urllib.request.urlopen", return_value=mock_resp):
            curve = adapter.yield_curve("20260501", use_cache=False)
        for date in curve.dates:
            assert 0.0 < curve.df(date) <= 1.0
