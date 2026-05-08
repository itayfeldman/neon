import math
from datetime import datetime

import numpy as np

from neon.lib.core.constants import DATE_FORMAT


class DiscountCurve:
    def __init__(
        self,
        value_date: str,
        dates: list[str],
        zero_rates: list[float],
    ) -> None:
        self._value_date = datetime.strptime(value_date, DATE_FORMAT)
        self._dates = [datetime.strptime(d, DATE_FORMAT) for d in dates]
        self._zero_rates = zero_rates
        self._times = [self._years(d) for d in self._dates]
        self._log_dfs = [-r * t for r, t in zip(zero_rates, self._times)]

    @property
    def value_date(self) -> str:
        return self._value_date.strftime(DATE_FORMAT)

    @property
    def dates(self) -> list[str]:
        return [d.strftime(DATE_FORMAT) for d in self._dates]

    @property
    def zero_rates(self) -> list[float]:
        return list(self._zero_rates)

    def _years(self, date: datetime) -> float:
        return (date - self._value_date).days / 365.0

    def _years_from_value(self, date: str) -> float:
        return self._years(datetime.strptime(date, DATE_FORMAT))

    def df(self, date: str) -> float:
        t = self._years_from_value(date)
        if t <= 0:
            return 1.0
        log_df = float(np.interp(t, self._times, self._log_dfs))
        return float(math.exp(log_df))

    def zero_rate(self, date: str) -> float:
        t = self._years_from_value(date)
        if t <= 0:
            return float(self._zero_rates[0])
        return float(-math.log(self.df(date)) / t)

    def forward_rate(self, date1: str, date2: str) -> float:
        t1 = self._years_from_value(date1)
        t2 = self._years_from_value(date2)
        log_df1 = math.log(self.df(date1)) if t1 > 0 else 0.0
        log_df2 = math.log(self.df(date2))
        return float((log_df1 - log_df2) / (t2 - t1))
