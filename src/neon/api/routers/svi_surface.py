from datetime import datetime

import pandas as pd
import yfinance as yf
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from neon.lib.data.yahoo import YahooFinanceAdapter
from neon.lib.instruments.surface.svi import SVICalibrator, SVISurface

router = APIRouter(prefix="/stock", tags=["svi-surface"])
_adapter = YahooFinanceAdapter()

_MAX_EXPIRIES = 8


class SurfaceResponse(BaseModel):
    strikes: list[float]
    expiries: list[str]
    vols: list[list[float]]


def _time_to_expiry(expiry: str, today: pd.Timestamp) -> float:
    d = datetime.strptime(expiry, "%Y-%m-%d")
    return max((d - today.to_pydatetime()).days, 1) / 365.0


@router.get("/{ticker}/svi-surface", response_model=SurfaceResponse)
def get_svi_surface(ticker: str) -> SurfaceResponse:
    try:
        tk = yf.Ticker(ticker)
        expiry_dates = tk.options
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if not expiry_dates:
        raise HTTPException(status_code=404, detail=f"No options found for {ticker}")

    try:
        spot = _adapter.spot(ticker)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    today = pd.Timestamp.today().normalize()
    market_data: dict[str, tuple[list[float], list[float]]] = {}
    forwards: dict[str, float] = {}
    times: dict[str, float] = {}

    for expiry in expiry_dates[:_MAX_EXPIRIES]:
        try:
            chain = tk.option_chain(expiry)
        except Exception:
            continue

        valid = chain.calls[
            chain.calls["impliedVolatility"].notna()
            & (chain.calls["impliedVolatility"] > 0.01)
        ]
        if len(valid) < 3:
            continue

        strikes = valid["strike"].astype(float).tolist()
        vols = valid["impliedVolatility"].astype(float).tolist()
        T = _time_to_expiry(expiry, today)

        try:
            SVICalibrator.fit(strikes, spot, T, vols)
        except Exception:
            continue

        market_data[expiry] = (strikes, vols)
        forwards[expiry] = spot
        times[expiry] = T

    if not market_data:
        raise HTTPException(
            status_code=404,
            detail=f"SVI calibration failed for all expiries of {ticker}",
        )

    surface = SVISurface.calibrate(market_data, forwards, times)
    strike_grid = sorted({s for strikes, _ in market_data.values() for s in strikes})
    expiry_grid = sorted(market_data.keys())

    vols_grid = [
        [round(surface.get_vol(s, e), 6) for e in expiry_grid]
        for s in strike_grid
    ]

    return SurfaceResponse(strikes=strike_grid, expiries=expiry_grid, vols=vols_grid)
