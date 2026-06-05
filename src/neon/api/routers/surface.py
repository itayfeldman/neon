import yfinance as yf
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from neon.lib.data.yahoo import YahooFinanceAdapter

router = APIRouter(prefix="/stock", tags=["surface"])
_adapter = YahooFinanceAdapter()


class SurfaceResponse(BaseModel):
    strikes: list[float]
    expiries: list[str]
    vols: list[list[float]]


@router.get("/{ticker}/surface", response_model=SurfaceResponse)
def get_surface(ticker: str) -> SurfaceResponse:
    try:
        tk = yf.Ticker(ticker)
        expiry_dates = tk.options
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if not expiry_dates:
        raise HTTPException(status_code=404, detail=f"No options found for {ticker}")

    strike_iv: dict[float, dict[str, float]] = {}
    for expiry in expiry_dates[:8]:
        try:
            chain = tk.option_chain(expiry)
        except Exception:
            continue
        for _, row in chain.calls.iterrows():
            strike = float(row["strike"])
            iv = float(row.get("impliedVolatility") or 0.0)
            if iv > 0:
                strike_iv.setdefault(strike, {})[expiry] = iv

    if not strike_iv:
        raise HTTPException(
            status_code=404, detail=f"No IV data available for {ticker}"
        )

    strikes = sorted(strike_iv)
    expiries = sorted({e for ivs in strike_iv.values() for e in ivs})
    vols = [
        [strike_iv.get(s, {}).get(e, 0.0) for e in expiries]
        for s in strikes
    ]
    return SurfaceResponse(strikes=strikes, expiries=expiries, vols=vols)
