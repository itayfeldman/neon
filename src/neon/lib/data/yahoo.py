import pandas as pd
import yfinance as yf

from neon.lib.data import cache
from neon.lib.data.base import DataAdapter, DataFetchError
from neon.lib.instruments.options.option_inputs import OptionInputs
from neon.lib.instruments.options.option_type import OptionType

_PROVIDER = "yahoo"
_TTL = 24 * 3600  # 1 day


class YahooFinanceAdapter(DataAdapter):
    def fetch(
        self, ticker: str, *, period: str = "1y", use_cache: bool = True
    ) -> pd.DataFrame:
        """
        Fetch OHLCV history for a ticker.
        Returns a DataFrame with columns: date, open, high, low, close, volume.
        """
        params = {"ticker": ticker, "period": period}
        if use_cache:
            cached = cache.load(_PROVIDER, params, _TTL)
            if cached is not None:
                return cached

        try:
            raw = yf.download(ticker, period=period, auto_adjust=True, progress=False)
        except Exception as exc:
            raise DataFetchError(f"Yahoo fetch failed for {ticker}: {exc}") from exc

        if raw.empty:
            raise DataFetchError(f"No data returned for {ticker}")

        df = raw.copy()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
        df.columns = [c.lower() for c in df.columns]
        df = df.reset_index().rename(columns={"Date": "date", "index": "date"})
        df["date"] = pd.to_datetime(df["date"])

        if use_cache:
            cache.save(_PROVIDER, params, df)
        return df

    def to_domain(self, df: pd.DataFrame) -> pd.DataFrame:
        return df

    def spot(self, ticker: str) -> float:
        """Return the most recent closing price."""
        df = self.fetch(ticker, period="5d")
        return float(df["close"].iloc[-1])

    def option_chain(
        self,
        ticker: str,
        expiry: str,
        risk_free_rate: float = 0.05,
        volatility: float = 0.2,
    ) -> list[OptionInputs]:
        """
        Fetch the options chain for a given expiry and map to OptionInputs.
        `expiry` must be in YYYY-MM-DD format as returned by yfinance.
        """
        try:
            tk = yf.Ticker(ticker)
            chain = tk.option_chain(expiry)
        except Exception as exc:
            raise DataFetchError(
                f"Yahoo option chain failed for {ticker}/{expiry}: {exc}"
            ) from exc

        spot = self.spot(ticker)
        current_date = pd.Timestamp.today().strftime("%Y%m%d")
        expiry_date = expiry.replace("-", "")

        inputs = []
        for _, row in chain.calls.iterrows():
            inputs.append(OptionInputs(
                underlying_ticker=ticker,
                underlying_price=spot,
                strike_price=float(row["strike"]),
                volatility=float(row["impliedVolatility"]) or volatility,
                risk_free_rate=risk_free_rate,
                current_date=current_date,
                expiry_date=expiry_date,
                option_type=OptionType.Call,
            ))
        for _, row in chain.puts.iterrows():
            inputs.append(OptionInputs(
                underlying_ticker=ticker,
                underlying_price=spot,
                strike_price=float(row["strike"]),
                volatility=float(row["impliedVolatility"]) or volatility,
                risk_free_rate=risk_free_rate,
                current_date=current_date,
                expiry_date=expiry_date,
                option_type=OptionType.Put,
            ))
        return inputs
