from neon.lib.datetime.day_count import DayCount
from neon.lib.fixed_income.coupon_schedule import CouponSchedule

# Guardrail for near-zero discount factors that are numerically unstable/unrealistic.
_MIN_DF = 1e-10


class Swap:
    def __init__(
        self,
        value_date: str,
        maturity_date: str,
        fixed_rate: float,
        coupon_freq: int = 2,
        day_count: DayCount = DayCount.ACT365,
    ) -> None:
        self._value_date = value_date
        self._maturity_date = maturity_date
        self._fixed_rate = fixed_rate
        self._coupon_freq = coupon_freq
        self._day_count = day_count
        self._schedule = CouponSchedule(value_date, maturity_date, coupon_freq)

    def discount_factor(self, curve: object) -> tuple[str, float]:
        c = self._fixed_rate / self._coupon_freq
        coupon_dates = self._schedule.payment_dates
        # Sum df for all coupon dates except the maturity (which is unknown)
        annuity = sum(curve.df(d) for d in coupon_dates[:-1])
        # Solve par condition: c * (annuity + df_T) + df_T = 1
        # => df_T * (c + 1) = 1 - c * annuity
        df_T = float((1 - c * annuity) / (1 + c))
        if not (_MIN_DF < df_T <= 1.0):
            raise ValueError(
                "Invalid terminal discount factor "
                f"{df_T} for swap maturity {self._maturity_date}; "
                f"expected {_MIN_DF} < df_T <= 1"
            )
        return self._maturity_date, df_T
