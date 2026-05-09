class Greeks:
    underlying_price: float
    strike_price: float
    volatility: float
    risk_free_rate: float
    time_to_maturity: float
    option_type: int

    def delta(self) -> float:
        return 1.0

    def gamma(self) -> float:
        return 0.0

    def rho(self) -> float:
        return 0.0

    def theta(self) -> float:
        return 0.0

    def vanna(self) -> float:
        return 0.0

    def vega(self) -> float:
        return 0.0

    def volga(self) -> float:
        return 0.0
