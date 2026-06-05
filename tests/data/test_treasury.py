from unittest.mock import patch

import pytest

from neon.lib.data.treasury import USTreasuryAdapter, _parse_xml
from neon.lib.fixed_income.discount_curve import DiscountCurve
from tests.data.conftest import TREASURY_XML


class TestParseXml:
    def test_returns_expected_columns(self):
        df = _parse_xml(TREASURY_XML)
        assert "date" in df.columns
        assert "BC_1YEAR" in df.columns

    def test_yields_are_floats(self):
        df = _parse_xml(TREASURY_XML)
        assert df["BC_10YEAR"].dtype == float

    def test_sorted_by_date(self):
        df = _parse_xml(TREASURY_XML)
        assert list(df["date"]) == sorted(df["date"])


class TestFetch:
    def test_returns_dataframe_from_mocked_url(self):
        adapter = USTreasuryAdapter()
        with patch("urllib.request.urlopen") as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = (
                TREASURY_XML
            )
            df = adapter.fetch("20260501", use_cache=False)
        assert not df.empty
        assert "BC_10YEAR" in df.columns

    def test_raises_data_fetch_error_on_network_failure(self):
        from neon.lib.data.base import DataFetchError
        adapter = USTreasuryAdapter()
        with patch("urllib.request.urlopen", side_effect=OSError("timeout")):
            with pytest.raises(DataFetchError):
                adapter.fetch("20260501", use_cache=False)


class TestToDomain:
    def test_returns_discount_curve(self, treasury_df):
        adapter = USTreasuryAdapter()
        curve = adapter.to_domain(treasury_df, "20260501")
        assert isinstance(curve, DiscountCurve)

    def test_discount_factors_are_valid(self, treasury_df):
        adapter = USTreasuryAdapter()
        curve = adapter.to_domain(treasury_df, "20260501")
        for date in curve.dates:
            assert 0.0 < curve.df(date) <= 1.0

    def test_curve_has_expected_tenors(self, treasury_df):
        adapter = USTreasuryAdapter()
        curve = adapter.to_domain(treasury_df, "20260501")
        assert len(curve.dates) == len(curve.zero_rates)
        assert len(curve.dates) > 0
