from neon.lib.portfolio.portfolio import Portfolio


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
