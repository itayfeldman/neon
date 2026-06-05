from datetime import date

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from neon.lib.data.base import DataFetchError
from neon.lib.data.yahoo import YahooFinanceAdapter
from neon.lib.greeks.analytical_greeks import AnalyticalGreeks
from neon.lib.instruments.options.european import EuropeanOption
from neon.lib.instruments.options.option_inputs import OptionInputs
from neon.lib.instruments.options.option_type import OptionType
from neon.lib.portfolio.portfolio import Portfolio
from neon.lib.portfolio.position import Position
from neon.lib.risk.risk_engine import RiskEngine

router = APIRouter(prefix="/portfolio", tags=["portfolio"])
_adapter = YahooFinanceAdapter()

_FALLBACK_VOL = 0.2
_FALLBACK_RATE = 0.05


class PositionRequest(BaseModel):
    ticker: str
    expiry: str        # YYYY-MM-DD
    strike: float
    option_type: str   # "call" or "put"
    quantity: float


class PortfolioRequest(BaseModel):
    positions: list[PositionRequest]


class GreeksResponse(BaseModel):
    delta: float
    gamma: float
    vega: float
    theta: float


def _resolve_vol(
    ticker: str, expiry: str, strike: float, option_type: OptionType
) -> float:
    try:
        chain = _adapter.option_chain(ticker, expiry)
    except DataFetchError:
        return _FALLBACK_VOL
    for inp in chain:
        if inp.strike_price == strike and inp.option_type == option_type:
            return inp.volatility if inp.volatility > 0 else _FALLBACK_VOL
    return _FALLBACK_VOL


def _build_position(req: PositionRequest) -> Position:
    if req.option_type not in ("call", "put"):
        raise ValueError(
            f"option_type must be 'call' or 'put', got {req.option_type!r}"
        )

    opt_type = OptionType.Call if req.option_type == "call" else OptionType.Put
    expiry_compact = req.expiry.replace("-", "")
    current_compact = date.today().strftime("%Y%m%d")

    vol = _resolve_vol(req.ticker, req.expiry, req.strike, opt_type)

    inputs = OptionInputs(
        underlying_ticker=req.ticker,
        underlying_price=_adapter.spot(req.ticker),
        strike_price=req.strike,
        volatility=vol,
        risk_free_rate=_FALLBACK_RATE,
        current_date=current_compact,
        expiry_date=expiry_compact,
        option_type=opt_type,
    )
    return Position(
        instrument=EuropeanOption(inputs, AnalyticalGreeks()), quantity=req.quantity
    )


@router.post("/greeks", response_model=GreeksResponse)
def get_portfolio_greeks(body: PortfolioRequest) -> GreeksResponse:
    if not body.positions:
        return GreeksResponse(delta=0.0, gamma=0.0, vega=0.0, theta=0.0)

    portfolio = Portfolio(name="api")
    for req in body.positions:
        try:
            portfolio.add_position(_build_position(req))
        except (ValueError, DataFetchError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    engine = RiskEngine(portfolio)
    return GreeksResponse(
        delta=engine.net_delta(),
        gamma=engine.net_gamma(),
        vega=engine.net_vega(),
        theta=engine.net_theta(),
    )
