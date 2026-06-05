import yfinance as yf
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from neon.lib.data.yahoo import YahooFinanceAdapter

router = APIRouter(prefix="/stock", tags=["options"])
_adapter = YahooFinanceAdapter()


class OptionRow(BaseModel):
    strike: float
    iv: float
    bid: float
    ask: float
    volume: int
    open_interest: int
    option_type: str


class OptionsResponse(BaseModel):
    calls: list[OptionRow]
    puts: list[OptionRow]


@router.get("/{ticker}/options/{expiry}", response_model=OptionsResponse)
def get_options(ticker: str, expiry: str) -> OptionsResponse:
    try:
        tk = yf.Ticker(ticker)
        chain = tk.option_chain(expiry)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    def _rows(df, option_type: str) -> list[OptionRow]:
        return [
            OptionRow(
                strike=float(r["strike"]),
                iv=float(r.get("impliedVolatility") or 0.0),
                bid=float(r.get("bid") or 0.0),
                ask=float(r.get("ask") or 0.0),
                volume=int(r.get("volume") or 0),
                open_interest=int(r.get("openInterest") or 0),
                option_type=option_type,
            )
            for _, r in df.iterrows()
        ]

    return OptionsResponse(
        calls=_rows(chain.calls, "call"),
        puts=_rows(chain.puts, "put"),
    )
