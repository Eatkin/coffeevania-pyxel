from typing import Any

import pyxel

from coffeevania.components.collision import CollisionRectangle
from coffeevania.components.position import Position
from coffeevania.components.velocity import Velocity
from coffeevania.game_objects.basic import Hazard


class BouncingHazard(Hazard):
    position: Position
    REQUIRED = ("position",)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.collision = CollisionRectangle(4, 4, 2, 2)
        self.velocity = Velocity(xspeed=2)

    def update(self) -> None:
        self.position.x += self.velocity.xspeed * self.speed_factor
        if self.position.x <= 0 or self.position.x >= 152:
            self.velocity.xspeed *= -1

    def draw(self) -> None:
        r = 4
        pyxel.circ(self.position.x + r, self.position.y + r, r, pyxel.COLOR_RED)
