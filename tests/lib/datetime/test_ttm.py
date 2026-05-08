import pytest

from neon.lib.datetime.day_count import DayCount
from neon.lib.datetime.ttm import time_to_maturity


class TestActActIsda:
    def test_same_year_non_leap(self):
        # 2023 is not a leap year: 365 days
        # Jan 1 to Jul 1 = 181 days → 181/365
        result = time_to_maturity("20230101", "20230701", DayCount.ACTACT_ISDA)
        assert result == pytest.approx(181 / 365, rel=1e-6)

    def test_same_year_leap(self):
        # 2024 is a leap year: 366 days
        # Jan 1 to Jul 1 = 182 days → 182/366
        result = time_to_maturity("20240101", "20240701", DayCount.ACTACT_ISDA)
        assert result == pytest.approx(182 / 366, rel=1e-6)

    def test_spanning_year_boundary(self):
        # Jul 1 2023 to Jul 1 2024: spans non-leap→leap boundary
        # 2023 portion: Jul 1–Dec 31 = 184 days in non-leap year (365)
        # 2024 portion: Jan 1–Jul 1  = 182 days in leap year (366)
        result = time_to_maturity("20230701", "20240701", DayCount.ACTACT_ISDA)
        expected = 184 / 365 + 182 / 366
        assert result == pytest.approx(expected, rel=1e-6)

    def test_differs_from_act365_across_leap_year(self):
        # Spanning a leap year should give a different result than ACT/365
        act_act = time_to_maturity("20230701", "20240701", DayCount.ACTACT_ISDA)
        act_365 = time_to_maturity("20230701", "20240701", DayCount.ACT365)
        assert act_act != pytest.approx(act_365, rel=1e-4)

    def test_one_full_non_leap_year(self):
        result = time_to_maturity("20230101", "20240101", DayCount.ACTACT_ISDA)
        assert result == pytest.approx(1.0, rel=1e-6)

    def test_one_full_leap_year(self):
        result = time_to_maturity("20240101", "20250101", DayCount.ACTACT_ISDA)
        assert result == pytest.approx(1.0, rel=1e-6)
