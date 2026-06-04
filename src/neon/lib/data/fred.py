import os
from datetime import datetime, timedelta

import pandas as pd

from neon.lib.core.constants import DATE_FORMAT
from neon.lib.data import cache
from neon.lib.data.base import DataAdapter, DataFetchError
from neon.lib.fixed_income.discount_curve import DiscountCurve

_PROVIDER = "fred"
_TTL_SERIES = 24 * 3600       # 1 day
_TTL_CURVE = 7 * 24 * 3600    # 7 days

# FRED series IDs for the par Treasury yield curve
_CURVE_SERIES = {
    "DGS1MO": 1 / 12,
    "DGS3MO": 3 / 12,
    "DGS6MO": 6 / 12,
    "DGS1": 1.0,
    "DGS2": 2.0,
    "DGS3": 3.0,
    "DGS5": 5.0,
    "DGS7": 7.0,
    "DGS10": 10.0,
    "DGS20": 20.0,
    "DGS30": 30.0,
}


class FREDAdapter(DataAdapter):
    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or os.environ.get("FRED_API_KEY")
        if not self._api_key:
            raise ValueError("FRED_API_KEY must be set or passed as api_key")

    def fetch(self, series_id: str, *, use_cache: bool = True) -> pd.DataFrame:
        """
        Fetch a FRED time series by ID.
        Returns a DataFrame with columns: date, value.
        """
        params = {"series_id": series_id}
        if use_cache:
            cached = cache.load(_PROVIDER, params, _TTL_SERIES)
            if cached is not None:
                return cached

        try:
            import json
            import urllib.request
            url = (
                f"https://api.stlouisfed.org/fred/series/observations"
                f"?series_id={series_id}&api_key={self._api_key}&file_type=json"
            )
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read())
        except Exception as exc:
            raise DataFetchError(f"FRED fetch failed for {series_id}: {exc}") from exc

        observations = data.get("observations", [])
        df = pd.DataFrame(observations)[["date", "value"]]
        df["date"] = pd.to_datetime(df["date"])
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df.dropna().reset_index(drop=True)

        if use_cache:
            cache.save(_PROVIDER, params, df)
        return df

    def to_domain(self, df: pd.DataFrame) -> pd.Series:
        return df.set_index("date")["value"]

    def yield_curve(self, date: str, *, use_cache: bool = True) -> DiscountCurve:
        """Fetch all curve series and build a DiscountCurve for the given date."""
        params = {"type": "yield_curve", "date": date}
        if use_cache:
            cached = cache.load(_PROVIDER, params, _TTL_CURVE)
            if cached is not None:
                return _df_to_curve(cached, date)

        rows = []
        for series_id, tenor_years in _CURVE_SERIES.items():
            df = self.fetch(series_id, use_cache=use_cache)
            dt = datetime.strptime(date, DATE_FORMAT)
            closest = df.iloc[(df["date"] - dt).abs().argsort()[:1]]
            if closest.empty:
                continue
            rate = closest.iloc[0]["value"] / 100.0
            rows.append({"tenor_years": tenor_years, "rate": rate})

        df_curve = pd.DataFrame(rows)
        if use_cache:
            cache.save(_PROVIDER, params, df_curve)
        return _df_to_curve(df_curve, date)


def _df_to_curve(df: pd.DataFrame, date: str) -> DiscountCurve:
    value_dt = datetime.strptime(date, DATE_FORMAT)
    dates = [
        (value_dt + timedelta(days=int(r["tenor_years"] * 365))).strftime(DATE_FORMAT)
        for _, r in df.iterrows()
    ]
    zero_rates = list(df["rate"])
    return DiscountCurve(value_date=date, dates=dates, zero_rates=zero_rates)
