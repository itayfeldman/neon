from datetime import date

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

from neon.lib.fixed_income.bond import Bond
from neon.lib.fixed_income.bond_analytics import BondAnalytics

router = APIRouter(prefix="/bonds", tags=["bonds"])


class BondRequest(BaseModel):
    face_value: float = 1000.0
    coupon_rate: float
    coupon_freq: int = 2
    issue_date: str   # YYYYMMDD
    maturity_date: str
    ytm: float

    @field_validator("coupon_rate", "ytm")
    @classmethod
    def must_be_in_unit_interval(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("must be between 0 and 1")
        return v


class BondResponse(BaseModel):
    dirty_price: float
    clean_price: float
    accrued_interest: float
    modified_duration: float
    macaulay_duration: float
    dv01: float
    convexity: float


@router.post("/price", response_model=BondResponse)
def price_bond(body: BondRequest) -> BondResponse:
    try:
        bond = Bond(
            issue_date=body.issue_date,
            maturity_date=body.maturity_date,
            coupon_rate=body.coupon_rate,
            coupon_freq=body.coupon_freq,
            face=body.face_value,
        )
        settle = date.today().strftime("%Y%m%d")
        analytics = BondAnalytics(bond)
        return BondResponse(
            dirty_price=bond.dirty_price_from_ytm(settle, body.ytm),
            clean_price=bond.clean_price_from_ytm(settle, body.ytm),
            accrued_interest=bond.accrued_interest(settle),
            modified_duration=analytics.modified_duration(settle, body.ytm),
            macaulay_duration=analytics.macaulay_duration(settle, body.ytm),
            dv01=analytics.dv01(settle, body.ytm),
            convexity=analytics.convexity(settle, body.ytm),
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
