from neon.lib.datetime.day_count import DayCount
from neon.lib.fixed_income.coupon_schedule import CouponSchedule


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

        if df_T <= 0:
            raise ValueError(
                f"Invalid bootstrapped discount factor for maturity "
                f"{self._maturity_date}: computed df={df_T} from fixed_rate="
                f"{self._fixed_rate} and annuity={annuity}. Expected df > 0."
            )

        if len(coupon_dates) > 1:
            last_coupon_date = coupon_dates[-2]
            last_coupon_df = float(curve.df(last_coupon_date))
            if df_T > last_coupon_df:
                raise ValueError(
                    f"Invalid bootstrapped discount factor for maturity "
                    f"{self._maturity_date}: computed df={df_T} exceeds the "
                    f"discount factor at the last coupon date "
                    f"{last_coupon_date} ({last_coupon_df}). This suggests "
                    f"an inconsistent input curve or extreme fixed_rate="
                    f"{self._fixed_rate}."
                )

        return self._maturity_date, df_T
