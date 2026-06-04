from dataclasses import dataclass

from neon.lib.instruments.instrument import Instrument


@dataclass(frozen=True, slots=True)
class Position:
    instrument: Instrument
    quantity: float

    def value(self) -> float:
        return self.instrument.price() * self.quantity * self.instrument.multiplier
