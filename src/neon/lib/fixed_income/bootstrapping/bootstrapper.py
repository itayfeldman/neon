import math
from datetime import datetime

from neon.lib.core.constants import DATE_FORMAT
from neon.lib.fixed_income.discount_curve import DiscountCurve


class CurveBootstrapper:
    def __init__(self, value_date: str, instruments: list) -> None:
        self._value_date = value_date
        self._instruments = instruments

    def build(self) -> DiscountCurve:
        empty = _empty_curve(self._value_date)
        sorted_instruments = sorted(
            self._instruments,
            key=lambda inst: inst.discount_factor(empty)[0],
        )

        dates: list[str] = []
        zero_rates: list[float] = []
        curve = empty

        for instrument in sorted_instruments:
            date, df = instrument.discount_factor(curve)
            t = self._years(date)
            zero_rate = -math.log(df) / t if t > 0 else 0.0
            dates.append(date)
            zero_rates.append(zero_rate)
            curve = DiscountCurve(self._value_date, dates, zero_rates)

        return curve

    def _years(self, date: str) -> float:
        value = datetime.strptime(self._value_date, DATE_FORMAT)
        end = datetime.strptime(date, DATE_FORMAT)
        return (end - value).days / 365.0


def _empty_curve(value_date: str) -> DiscountCurve:
    return DiscountCurve(value_date, [value_date], [0.0])
