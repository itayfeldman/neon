from neon.lib.fixed_income.coupon_schedule import CouponSchedule


class TestPaymentDates:
    def test_maturity_is_last_date(self):
        sched = CouponSchedule("20200101", "20250101", coupon_freq=2)
        assert sched.payment_dates[-1] == "20250101"

    def test_semi_annual_count(self):
        # 5-year semi-annual: 10 payments
        sched = CouponSchedule("20200101", "20250101", coupon_freq=2)
        assert len(sched.payment_dates) == 10

    def test_annual_count(self):
        # 5-year annual: 5 payments
        sched = CouponSchedule("20200101", "20250101", coupon_freq=1)
        assert len(sched.payment_dates) == 5

    def test_quarterly_count(self):
        # 2-year quarterly: 8 payments
        sched = CouponSchedule("20230101", "20250101", coupon_freq=4)
        assert len(sched.payment_dates) == 8

    def test_dates_ascending(self):
        sched = CouponSchedule("20200101", "20250101", coupon_freq=2)
        dates = sched.payment_dates
        assert dates == sorted(dates)

    def test_dates_after_issue(self):
        sched = CouponSchedule("20200101", "20250101", coupon_freq=2)
        for d in sched.payment_dates:
            assert d > "20200101"

    def test_semi_annual_spacing(self):
        sched = CouponSchedule("20200101", "20250101", coupon_freq=2)
        dates = sched.payment_dates
        # First payment should be 6 months before maturity last step
        assert dates[-2] == "20240701"
        assert dates[-1] == "20250101"
