from dataclasses import dataclass

from neon.lib.fixed_income.bond import Bond
from neon.lib.fixed_income.bond_analytics import BondAnalytics
from neon.lib.portfolio.portfolio import Portfolio

_BP = 0.0001


@dataclass
class BondRisk:
    dv01: float
    modified_duration: float
    convexity: float
    spread_dv01: float


class RiskEngine:
    def __init__(self, portfolio: Portfolio) -> None:
        self._portfolio = portfolio

    def net_delta(self) -> float:
        return float(
            sum(
                p.quantity * p.instrument.greeks.delta()
                for p in self._portfolio.positions
            )
        )

    def net_gamma(self) -> float:
        return float(
            sum(
                p.quantity * p.instrument.greeks.gamma()
                for p in self._portfolio.positions
            )
        )

    def net_vega(self) -> float:
        return float(
            sum(
                p.quantity * p.instrument.greeks.vega()
                for p in self._portfolio.positions
            )
        )

    def net_theta(self) -> float:
        return float(
            sum(
                p.quantity * p.instrument.greeks.theta()
                for p in self._portfolio.positions
            )
        )

    def net_rho(self) -> float:
        return float(
            sum(
                p.quantity * p.instrument.greeks.rho()
                for p in self._portfolio.positions
            )
        )

    def net_vanna(self) -> float:
        return float(
            sum(
                p.quantity * p.instrument.greeks.vanna()
                for p in self._portfolio.positions
            )
        )

    def net_volga(self) -> float:
        return float(
            sum(
                p.quantity * p.instrument.greeks.volga()
                for p in self._portfolio.positions
            )
        )

    def bond_risk(
        self,
        settle_date: str,
        ytms: dict[Bond, float],
        spreads: dict[Bond, float] | None = None,
    ) -> BondRisk:
        if spreads is None:
            spreads = {}

        bond_positions = [
            p for p in self._portfolio.positions
            if isinstance(p.instrument, Bond)
        ]
        missing_ytms = [
            p.instrument for p in bond_positions
            if p.instrument not in ytms
        ]
        if missing_ytms:
            raise ValueError(
                f"Missing YTM entries for {len(missing_ytms)} bond(s) in portfolio"
            )

        total_dv01 = 0.0
        total_spread_dv01 = 0.0
        total_dirty_value = 0.0
        weighted_duration = 0.0
        weighted_convexity = 0.0

        for p in bond_positions:
            bond = p.instrument
            ytm = ytms[bond]
            spread = spreads.get(bond, 0.0)
            analytics = BondAnalytics(bond)

            dirty = bond.dirty_price_from_ytm(settle_date, ytm + spread)
            position_value = abs(p.quantity) * dirty

            dv01 = p.quantity * analytics.dv01(settle_date, ytm + spread)
            mod_dur = analytics.modified_duration(settle_date, ytm + spread)
            conv = analytics.convexity(settle_date, ytm + spread)
            spread_dv01 = dv01

            total_dv01 += dv01
            total_spread_dv01 += spread_dv01
            weighted_duration += mod_dur * position_value
            weighted_convexity += conv * position_value
            total_dirty_value += position_value

        if total_dirty_value == 0.0:
            return BondRisk(
                dv01=0.0,
                modified_duration=0.0,
                convexity=0.0,
                spread_dv01=0.0,
            )

        return BondRisk(
            dv01=total_dv01,
            modified_duration=weighted_duration / total_dirty_value,
            convexity=weighted_convexity / total_dirty_value,
            spread_dv01=total_spread_dv01,
        )
