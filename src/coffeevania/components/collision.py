from dataclasses import dataclass

from coffeevania.components import Component
from coffeevania.components.position import Position

from coffeevania.utils import Rect

@dataclass
class Collision(Component):
    pass

@dataclass
class CollisionRectangle(Collision):
    width: float
    height: float
    offset_x: float = 0.0
    offset_y: float = 0.0
    solid: bool = False

    def get_rect(self, position: Position) -> Rect:
        return Rect(x1=position.x + self.offset_x, x2=position.x + self.offset_x + self.width, y1 = position.y + self.offset_y, y2 = position.y + self.offset_y + self.height)

