from neon.lib.datetime.day_count import DayCount
from neon.lib.fixed_income.bond import Bond


class FloatingRateNote(Bond):
    def __init__(
        self,
        issue_date: str,
        maturity_date: str,
        reference_rate: float,
        spread: float,
        coupon_freq: int = 2,
        day_count: DayCount = DayCount.ACT365,
        face: float = 100.0,
    ) -> None:
        self._reference_rate = reference_rate
        self._spread = spread
        super().__init__(
            issue_date=issue_date,
            maturity_date=maturity_date,
            coupon_rate=reference_rate + spread,
            coupon_freq=coupon_freq,
            day_count=day_count,
            face=face,
        )

    @property
    def reference_rate(self) -> float:
        return self._reference_rate

    @property
    def spread(self) -> float:
        return self._spread
