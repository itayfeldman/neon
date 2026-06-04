from neon.lib.datetime.day_count import DayCount
from neon.lib.datetime.ttm import time_to_maturity


class FRA:
    def __init__(
        self,
        start_date: str,
        end_date: str,
        rate: float,
        day_count: DayCount = DayCount.ACT360,
    ) -> None:
        self._start_date = start_date
        self._end_date = end_date
        self._rate = rate
        self._day_count = day_count

    def discount_factor(self, curve: object) -> tuple[str, float]:
        t = time_to_maturity(self._start_date, self._end_date, self._day_count)
        df_end = float(curve.df(self._start_date) / (1 + self._rate * t))
        return self._end_date, df_end
