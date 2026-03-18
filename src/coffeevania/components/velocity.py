from dataclasses import dataclass

from coffeevania.components import Component

@dataclass
class Velocity(Component):
    xspeed: float = 0.0
    yspeed: float = 0.0
    max_xspeed: float = 1.0
    max_yspeed: float = 2.0
