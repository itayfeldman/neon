from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from neon.lib.core.constants import DATE_FORMAT
from neon.lib.data.yahoo import YahooFinanceAdapter
from neon.lib.greeks.analytical_greeks import AnalyticalGreeks
from neon.lib.instruments.options.option_inputs import OptionInputs
from neon.lib.instruments.options.option_type import OptionType

router = APIRouter(prefix="/stock", tags=["greeks"])
_adapter = YahooFinanceAdapter()


class GreeksRow(BaseModel):
    strike: float
    option_type: str
    delta: float
    gamma: float
    vega: float
    theta: float


class GreeksResponse(BaseModel):
    rows: list[GreeksRow]


def _compute(inputs: OptionInputs) -> GreeksRow:
    t = (
        datetime.strptime(inputs.expiry_date, DATE_FORMAT)
        - datetime.strptime(inputs.current_date, DATE_FORMAT)
    ).days / 365.0

    ag = AnalyticalGreeks()
    ag.underlying_price = inputs.underlying_price
    ag.strike_price = inputs.strike_price
    ag.volatility = inputs.volatility
    ag.risk_free_rate = inputs.risk_free_rate
    ag.time_to_maturity = max(t, 1e-6)
    ag.option_type = inputs.option_type

    return GreeksRow(
        strike=inputs.strike_price,
        option_type="call" if inputs.option_type == OptionType.Call else "put",
        delta=ag.delta(),
        gamma=ag.gamma(),
        vega=ag.vega(),
        theta=ag.theta(),
    )


@router.get("/{ticker}/greeks/{expiry}", response_model=GreeksResponse)
def get_greeks(ticker: str, expiry: str) -> GreeksResponse:
    try:
        option_inputs = _adapter.option_chain(ticker, expiry)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    rows = [_compute(inp) for inp in option_inputs if inp.volatility > 0]
    return GreeksResponse(rows=rows)
