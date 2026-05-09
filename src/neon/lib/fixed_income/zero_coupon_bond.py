from neon.lib.datetime.day_count import DayCount
from neon.lib.fixed_income.bond import Bond


class ZeroCouponBond(Bond):
    def __init__(
        self,
        issue_date: str,
        maturity_date: str,
        day_count: DayCount = DayCount.ACT365,
        face: float = 100.0,
    ) -> None:
        super().__init__(
            issue_date=issue_date,
            maturity_date=maturity_date,
            coupon_rate=0.0,
            coupon_freq=1,
            day_count=day_count,
            face=face,
        )
