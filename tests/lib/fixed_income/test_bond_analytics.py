from neon.lib.fixed_income.bond import Bond
from neon.lib.fixed_income.bond_analytics import BondAnalytics


def _bond() -> Bond:
    return Bond(
        issue_date="20250101",
        maturity_date="20350101",
        coupon_rate=0.05,
        coupon_freq=2,
    )


def _analytics() -> BondAnalytics:
    return BondAnalytics(_bond())


SETTLE = "20250101"
YTM = 0.05


class TestDv01:
    def test_returns_float(self):
        assert isinstance(_analytics().dv01(SETTLE, YTM), float)

    def test_positive(self):
        assert _analytics().dv01(SETTLE, YTM) > 0

    def test_higher_ytm_lower_dv01(self):
        a = _analytics()
        assert a.dv01(SETTLE, 0.03) > a.dv01(SETTLE, 0.07)


class TestModifiedDuration:
    def test_returns_float(self):
        assert isinstance(_analytics().modified_duration(SETTLE, YTM), float)

    def test_positive(self):
        assert _analytics().modified_duration(SETTLE, YTM) > 0

    def test_longer_maturity_higher_duration(self):
        short = BondAnalytics(
            Bond("20250101", "20280101", 0.05, 2)
        ).modified_duration(SETTLE, YTM)
        long_ = BondAnalytics(
            Bond("20250101", "20350101", 0.05, 2)
        ).modified_duration(SETTLE, YTM)
        assert long_ > short


class TestMacaulayDuration:
    def test_returns_float(self):
        assert isinstance(_analytics().macaulay_duration(SETTLE, YTM), float)

    def test_ge_modified_duration(self):
        a = _analytics()
        assert a.macaulay_duration(SETTLE, YTM) >= a.modified_duration(SETTLE, YTM)


class TestConvexity:
    def test_returns_float(self):
        assert isinstance(_analytics().convexity(SETTLE, YTM), float)

    def test_positive(self):
        assert _analytics().convexity(SETTLE, YTM) > 0
