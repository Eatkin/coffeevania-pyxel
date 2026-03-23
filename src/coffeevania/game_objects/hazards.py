from typing import Any

import pyxel

from coffeevania.components.collision import CollisionRectangle
from coffeevania.components.position import Position
from coffeevania.components.velocity import Velocity
from coffeevania.game_objects.basic import CoffeevaniaEntity
from coffeevania.utils import Rect
from coffeevania.utils import rects_overlap


class Hazard(CoffeevaniaEntity):
    """Hazard base class for anything that will kill player"""

    position: Position
    position_history: Position
    collision: CollisionRectangle

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.position_history = Position(0, 0)


    def collided_with_player(self) -> bool:
        """Check if the region swept by hazard has intersected player"""
        if not self.context.player:
            return False
        player_rect = self.context.player.collision.get_rect(
            self.context.player.position
        )
        x1, x2 = (
            self.position.x + self.collision.offset_x,
            self.position_history.x + self.collision.offset_x,
        )
        x1, x2 = min(x1, x2), max(x1, x2) + self.collision.width
        y1, y2 = (
            self.position.y + self.collision.offset_y,
            self.position_history.y + self.collision.offset_y,
        )
        y1, y2 = min(y1, y2), max(y1, y2) + self.collision.height
        this_rect = Rect(x1, x2, y1, y2)
        return rects_overlap(player_rect, this_rect)

    def update(self) -> None:
        if not self.context.player:
            return

        if self.collided_with_player():
            self.context.player.die()


class BouncingHazard(Hazard):
    position: Position
    position_history: Position
    REQUIRED = ("position",)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.collision = CollisionRectangle(4, 4, 2, 2)
        self.velocity = Velocity(xspeed=20)

    def update(self) -> None:
        # Store previous position
        self.position_history.x = self.position.x
        self.position_history.y = self.position.y
        self.position.x += self.velocity.xspeed * self.speed_factor

        if self.position.x <= 0 or self.position.x >= 152:
            self.velocity.xspeed *= -1

        super().update()

    def draw(self) -> None:
        r = 4
        pyxel.circ(self.position.x + r, self.position.y + r, r, pyxel.COLOR_RED)
