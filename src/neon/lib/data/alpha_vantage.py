import json
import os
import urllib.request

import pandas as pd

from neon.lib.data import cache
from neon.lib.data.base import DataAdapter, DataFetchError

_PROVIDER = "alpha_vantage"
_TTL = 24 * 3600  # 1 day
_BASE_URL = "https://www.alphavantage.co/query"


class AlphaVantageAdapter(DataAdapter):
    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or os.environ.get("ALPHA_VANTAGE_API_KEY")
        if not self._api_key:
            raise ValueError("ALPHA_VANTAGE_API_KEY must be set or passed as api_key")

    def fetch(self, symbol: str, *, use_cache: bool = True) -> pd.DataFrame:
        """
        Fetch daily adjusted OHLCV for a symbol.
        Returns a DataFrame with columns: date, open, high, low, close, volume.
        """
        params = {"symbol": symbol, "function": "TIME_SERIES_DAILY"}
        if use_cache:
            cached = cache.load(_PROVIDER, params, _TTL)
            if cached is not None:
                return cached

        try:
            url = (
                f"{_BASE_URL}?function=TIME_SERIES_DAILY&symbol={symbol}"
                f"&outputsize=full&apikey={self._api_key}"
            )
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read())
        except Exception as exc:
            raise DataFetchError(
                f"Alpha Vantage fetch failed for {symbol}: {exc}"
            ) from exc

        if "Time Series (Daily)" not in data:
            detail = data.get("Note") or data.get("Information") or data
            raise DataFetchError(
                f"Unexpected Alpha Vantage response for {symbol}: {detail}"
            )

        ts = data["Time Series (Daily)"]
        rows = [
            {
                "date": pd.Timestamp(date),
                "open": float(vals["1. open"]),
                "high": float(vals["2. high"]),
                "low": float(vals["3. low"]),
                "close": float(vals["4. close"]),
                "volume": int(vals["5. volume"]),
            }
            for date, vals in ts.items()
        ]
        df = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)

        if use_cache:
            cache.save(_PROVIDER, params, df)
        return df

    def to_domain(self, df: pd.DataFrame) -> pd.DataFrame:
        return df

    def fx_rate(
        self, from_currency: str, to_currency: str, *, use_cache: bool = True
    ) -> float:
        """Return the current exchange rate between two currencies."""
        params = {
            "from": from_currency,
            "to": to_currency,
            "function": "CURRENCY_EXCHANGE_RATE",
        }
        if use_cache:
            cached = cache.load(_PROVIDER, params, _TTL)
            if cached is not None:
                return float(cached["rate"].iloc[0])

        try:
            url = (
                f"{_BASE_URL}?function=CURRENCY_EXCHANGE_RATE"
                f"&from_currency={from_currency}&to_currency={to_currency}"
                f"&apikey={self._api_key}"
            )
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read())
        except Exception as exc:
            raise DataFetchError(
                f"Alpha Vantage FX fetch failed ({from_currency}/{to_currency}): {exc}"
            ) from exc

        key = "Realtime Currency Exchange Rate"
        if key not in data:
            raise DataFetchError(f"Unexpected Alpha Vantage FX response: {data}")

        rate = float(data[key]["5. Exchange Rate"])
        if use_cache:
            cache.save(_PROVIDER, params, pd.DataFrame([{"rate": rate}]))
        return rate
