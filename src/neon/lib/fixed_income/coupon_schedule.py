from datetime import datetime

from dateutil.relativedelta import relativedelta

from neon.lib.core.constants import DATE_FORMAT


class CouponSchedule:
    def __init__(
        self,
        issue_date: str,
        maturity_date: str,
        coupon_freq: int,
    ) -> None:
        self._payment_dates = self._generate(issue_date, maturity_date, coupon_freq)

    @property
    def payment_dates(self) -> list[str]:
        return self._payment_dates

    @staticmethod
    def _generate(issue_date: str, maturity_date: str, coupon_freq: int) -> list[str]:
        months_step = 12 // coupon_freq
        issue = datetime.strptime(issue_date, DATE_FORMAT)
        maturity = datetime.strptime(maturity_date, DATE_FORMAT)

        dates = []
        current = maturity
        while current > issue:
            dates.append(current.strftime(DATE_FORMAT))
            current -= relativedelta(months=months_step)

        return list(reversed(dates))
