from dataclasses import dataclass

from coffeevania.components import Component

@dataclass
class Position(Component):
    x: float = 0.0
    y: float = 0.0
