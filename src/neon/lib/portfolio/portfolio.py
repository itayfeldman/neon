from dataclasses import dataclass, field

from neon.lib.portfolio.position import Position


@dataclass
class Portfolio:
    name: str
    positions: list[Position] = field(default_factory=list)

    def add_position(self, position: Position) -> None:
        self.positions.append(position)

    def value(self) -> float:
        return float(sum(p.value() for p in self.positions))
