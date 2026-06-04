from neon.lib.datetime.day_count import DayCount
from neon.lib.datetime.ttm import time_to_maturity


class Deposit:
    def __init__(
        self,
        value_date: str,
        maturity_date: str,
        rate: float,
        day_count: DayCount = DayCount.ACT360,
    ) -> None:
        self._value_date = value_date
        self._maturity_date = maturity_date
        self._rate = rate
        self._day_count = day_count

    def discount_factor(self, curve: object) -> tuple[str, float]:
        t = time_to_maturity(self._value_date, self._maturity_date, self._day_count)
        return self._maturity_date, float(1 / (1 + self._rate * t))
