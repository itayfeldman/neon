from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from neon.lib.data.base import DataFetchError
from neon.lib.data.yahoo import YahooFinanceAdapter

router = APIRouter(prefix="/stock", tags=["stock"])
_adapter = YahooFinanceAdapter()


class HistoryResponse(BaseModel):
    dates: list[str]
    opens: list[float]
    highs: list[float]
    lows: list[float]
    closes: list[float]
    volumes: list[int]


@router.get("/{ticker}/history", response_model=HistoryResponse)
def get_history(ticker: str, period: str = "1y") -> HistoryResponse:
    try:
        df = _adapter.fetch(ticker, period=period)
    except DataFetchError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return HistoryResponse(
        dates=df["date"].dt.strftime("%Y-%m-%d").tolist(),
        opens=df["open"].tolist(),
        highs=df["high"].tolist(),
        lows=df["low"].tolist(),
        closes=df["close"].tolist(),
        volumes=df["volume"].astype(int).tolist(),
    )
