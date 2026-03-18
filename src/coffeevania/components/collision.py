from dataclasses import dataclass

from coffeevania.components import Component

@dataclass
class Collision(Component):
    pass

@dataclass
class CollisionRectangle(Collision):
    width: float
    height: float
    offset_x: float = 0.0
    offset_y: float = 0.0

