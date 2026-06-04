from dataclasses import dataclass

from neon.lib.instruments.instrument import Instrument
from neon.lib.core.position_direction import PositionDirection


@dataclass(frozen=True, slots=True)
class Position:
    instrument: Instrument
    quantity: float
    direction: PositionDirection

    def value(self) -> float:
        return self.instrument.price() * self.quantity * self.instrument.multiplier * self.direction.value
