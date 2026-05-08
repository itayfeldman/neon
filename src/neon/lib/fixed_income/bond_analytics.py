from neon.lib.fixed_income.bond import Bond

_BP = 0.0001  # 1 basis point


class BondAnalytics:
    def __init__(self, bond: Bond) -> None:
        self._bond = bond

    def dv01(self, settle_date: str, ytm: float) -> float:
        p_up = self._bond.dirty_price_from_ytm(settle_date, ytm + _BP)
        p_dn = self._bond.dirty_price_from_ytm(settle_date, ytm - _BP)
        return float((p_dn - p_up) / 2)

    def modified_duration(self, settle_date: str, ytm: float) -> float:
        price = self._bond.dirty_price_from_ytm(settle_date, ytm)
        return float(self.dv01(settle_date, ytm) / price * 10000)

    def macaulay_duration(self, settle_date: str, ytm: float) -> float:
        mod_dur = self.modified_duration(settle_date, ytm)
        return float(mod_dur * (1 + ytm / self._bond._coupon_freq))

    def convexity(self, settle_date: str, ytm: float) -> float:
        price = self._bond.dirty_price_from_ytm(settle_date, ytm)
        p_up = self._bond.dirty_price_from_ytm(settle_date, ytm + _BP)
        p_dn = self._bond.dirty_price_from_ytm(settle_date, ytm - _BP)
        return float((p_up + p_dn - 2 * price) / (price * _BP**2))
