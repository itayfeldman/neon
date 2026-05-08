from dataclasses import dataclass

from neon.lib.instruments.instrument import Instrument


@dataclass(frozen=True)
class Position:
    instrument: Instrument
    quantity: float  # positive = long, negative = short

    def value(self) -> float:
        return self.instrument.price() * self.quantity
