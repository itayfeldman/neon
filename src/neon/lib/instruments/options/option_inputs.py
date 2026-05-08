from pydantic import BaseModel, Field

from neon.lib.core import Currency
from neon.lib.datetime import DayCount
from neon.lib.instruments.options.option_type import OptionType


# TODO: Move the reference to the underlying ticker to Position/Portfolio.
class OptionInputs(BaseModel):
    underlying_ticker: str = Field(
        ..., description="The ticker symbol of the underlying asset."
    )
    underlying_price: float = Field(
        ..., description="The current price of the underlying asset."
    )
    strike_price: float = Field(..., description="The strike price of the option.")
    volatility: float = Field(
        ..., description="The volatility of the underlying asset."
    )
    risk_free_rate: float = Field(..., description="The risk-free interest rate.")
    current_date: str = Field(..., description="The current date in YYYYMMDD format.")
    expiry_date: str = Field(
        ..., description="The expiration date of the option in YYYYMMDD format."
    )
    option_type: OptionType = Field(
        ..., description="The type of the option (call or put)."
    )
    multiplier: int = Field(1, description="The contract multiplier.")
    currency: Currency = Field(Currency.USD, description="The currency of the option.")
    day_count: DayCount = Field(
        DayCount.ACT365, description="The day count convention for time to maturity."
    )

    def unpack(self):
        return (
            self.underlying_price,
            self.strike_price,
            self.volatility,
            self.risk_free_rate,
            self.current_date,
            self.expiry_date,
            self.option_type,
            self.multiplier,
            self.currency,
            self.day_count,
        )
