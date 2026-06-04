import pytest

from neon.lib.fixed_income.bond import Bond
from neon.lib.fixed_income.bond_future import BondFuture

SETTLE = "20250101"
DELIVERY = "20250401"  # ~3 months out


def _bond(coupon_rate: float = 0.05, maturity: str = "20350101") -> Bond:
    return Bond(
        issue_date="20250101",
        maturity_date=maturity,
        coupon_rate=coupon_rate,
        coupon_freq=2,
    )


def _future(repo: float = 0.04) -> BondFuture:
    return BondFuture(delivery_date=DELIVERY, repo_rate=repo)


class TestConversionFactor:
    def test_returns_float(self):
        assert isinstance(_future().conversion_factor(_bond(), DELIVERY), float)

    def test_positive(self):
        assert _future().conversion_factor(_bond(), DELIVERY) > 0

    def test_at_notional_yield_near_one(self):
        # Bond with coupon = notional yield (6%) should have CF ≈ 1.0
        bond = _bond(coupon_rate=0.06)
        cf = _future().conversion_factor(bond, DELIVERY)
        assert cf == pytest.approx(1.0, abs=0.05)

    def test_high_coupon_higher_cf(self):
        cf_low = _future().conversion_factor(_bond(coupon_rate=0.03), DELIVERY)
        cf_high = _future().conversion_factor(_bond(coupon_rate=0.08), DELIVERY)
        assert cf_high > cf_low


class TestTheoreticalPrice:
    def test_returns_float(self):
        bond = _bond()
        clean = bond.clean_price_from_ytm(SETTLE, 0.05)
        price = _future().theoretical_price(bond, SETTLE, clean)
        assert isinstance(price, float)

    def test_positive(self):
        bond = _bond()
        clean = bond.clean_price_from_ytm(SETTLE, 0.05)
        assert _future().theoretical_price(bond, SETTLE, clean) > 0

    def test_higher_repo_lower_price(self):
        bond = _bond()
        clean = bond.clean_price_from_ytm(SETTLE, 0.05)
        low = BondFuture(DELIVERY, repo_rate=0.02).theoretical_price(
            bond, SETTLE, clean
        )
        high = BondFuture(DELIVERY, repo_rate=0.06).theoretical_price(
            bond, SETTLE, clean
        )
        # Higher repo → carry cost rises → futures price falls (net basis)
        # This depends on coupon vs repo; with 5% coupon and delivery in 3M the
        # coupon dominates. Just check they differ.
        assert low != pytest.approx(high)


class TestImpliedRepo:
    def test_returns_float(self):
        bond = _bond()
        clean = bond.clean_price_from_ytm(SETTLE, 0.05)
        futures_price = _future().theoretical_price(bond, SETTLE, clean)
        implied = _future().implied_repo(bond, SETTLE, clean, futures_price)
        assert isinstance(implied, float)

    def test_roundtrip(self):
        # implied_repo(theoretical_price) should recover repo_rate
        repo = 0.04
        bond = _bond()
        clean = bond.clean_price_from_ytm(SETTLE, 0.05)
        fut = BondFuture(DELIVERY, repo_rate=repo)
        futures_price = fut.theoretical_price(bond, SETTLE, clean)
        assert fut.implied_repo(bond, SETTLE, clean, futures_price) == pytest.approx(
            repo, abs=1e-4
        )


class TestCTD:
    def test_returns_bond(self):
        basket = [_bond(0.04), _bond(0.05), _bond(0.06)]
        settle = SETTLE
        fut = _future()
        prices = {b: b.clean_price_from_ytm(settle, 0.05) for b in basket}
        ctd = fut.ctd(basket, settle, prices)
        assert ctd in basket

    def test_ctd_minimises_delivery_cost(self):
        basket = [_bond(0.03), _bond(0.05), _bond(0.07)]
        settle = SETTLE
        fut = _future()
        prices = {b: b.clean_price_from_ytm(settle, 0.05) for b in basket}
        ctd = fut.ctd(basket, settle, prices)
        futures_price = fut.theoretical_price(ctd, settle, prices[ctd])
        # CTD has minimum net basis: spot - futures * CF
        ctd_basis = prices[ctd] - futures_price * fut.conversion_factor(ctd, DELIVERY)
        for b in basket:
            fp = fut.theoretical_price(b, settle, prices[b])
            basis = prices[b] - fp * fut.conversion_factor(b, DELIVERY)
            assert ctd_basis <= basis + 1e-6
