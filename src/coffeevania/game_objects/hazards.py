from __future__ import annotations

import math
from typing import Any

import pyxel

from coffeevania.common.game import GAME_WIDTH
from coffeevania.components.collision import CollisionRectangle
from coffeevania.components.position import Position
from coffeevania.components.sprites import Animation
from coffeevania.components.sprites import StaticSprite
from coffeevania.components.velocity import Velocity
from coffeevania.game.graphics import GRID_SIZE
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
        self.moves = True

    @property
    def swept_collision(self) -> Rect:
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
        return Rect(x1, x2, y1, y2)

    def collided_with_player(self) -> bool:
        """Check if the region swept by hazard has intersected player"""
        if not self.context.player:
            return False

        if not self.is_on_screen():
            return False

        player_rect = self.context.player.hurtbox.get_rect(self.context.player.position)

        # Simple collision for non-moving hazards
        if not self.moves:
            return rects_overlap(player_rect, self.collision.get_rect(self.position))

        return rects_overlap(player_rect, self.swept_collision)

    def update(self) -> None:
        if not self.context.player:
            return

        if self.collided_with_player():
            self.context.player.die()


class Spike(Hazard):
    position: Position
    position_history: Position
    REQUIRED = ("position",)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.collision = CollisionRectangle(8, 8, 0, 4)
        self.sprite = StaticSprite(sprite_name="Spike")
        self.moves = False

    def draw(self) -> None:
        self.sprite.draw(self.position)


class VerticalShooter(Hazard):
    position: Position
    REQUIRED = ("position",)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.collision = CollisionRectangle(4, 4, 2, 2)
        self.timer = 0.0
        self.speed = 0.01
        self.shoot_timer = 0.0
        self.shoot_rate = 3.0
        self.sprite = StaticSprite("VerticalShooter")

    def post_init(self) -> None:
        self._calculate_bounds()

    def _calculate_bounds(self) -> None:
        gx = int(self.position.x // GRID_SIZE)
        gy = int(self.position.y // GRID_SIZE)

        left_gx = gx
        while (left_gx - 1, gy) not in self.context.collision_map:
            left_gx -= 1
            if left_gx < 0:
                raise RuntimeError("You have an unbound vertical shooter")

        # Convert grid back to pixel (Left edge of current tile + offset)
        left_wall = left_gx * GRID_SIZE - self.collision.offset_x

        # 3. Look Right
        right_gx = gx
        while (right_gx + 1, gy) not in self.context.collision_map:
            right_gx += 1
            # Arbitrary break loop if I fuck something up
            if right_gx > GAME_WIDTH * 100:
                raise RuntimeError("You have an unbound vertical shooter")

        # Convert grid back to pixel (Right edge of current tile - width - offset)
        right_wall = (
            (right_gx * GRID_SIZE)
            + GRID_SIZE
            - self.collision.width
            - self.collision.offset_x
        )

        self.origin_x = (left_wall + right_wall) / 2
        self.amplitude = (right_wall - left_wall) / 2

        # Pre-calculate starting timer based on initial position
        offset = (self.position.x - self.origin_x) / max(self.amplitude, 1)
        # Clamp to avoid math domain errors in asin
        offset = max(-1, min(1, offset))
        self.timer = math.asin(offset) / (self.speed * 2 * math.pi)

    def update(self) -> None:
        self.timer += self.speed_factor
        self.position.x = self.origin_x + self.amplitude * pyxel.sin(
            self.timer * self.speed * 360
        )

        self.shoot_timer += self.speed_factor
        if self.shoot_timer >= self.shoot_rate:
            self.shoot_timer = 0
            self._shoot()

    def _shoot(self) -> None:
        self.context.app.create_entity(
            Bullet,
            position=Position(self.position.x, self.position.y),
            speed=10,
            angle=270,
        )

    def draw(self) -> None:
        self.sprite.draw(Position(self.position.x, self.position.y - 1))


class Bullet(Hazard):
    position: Position
    position_history: Position
    REQUIRED = ("position",)

    def __init__(self, speed: int, angle: int, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.collision = CollisionRectangle(4, 4, 2, 2)
        # Use -sin cause y-axis inverted in video games
        self.velocity = Velocity(
            xspeed=speed * pyxel.cos(angle), yspeed=-speed * pyxel.sin(angle)
        )
        self.sprite = StaticSprite(sprite_name="Bullet")

    def update(self) -> None:
        self.position_history.x = self.position.x
        self.position_history.y = self.position.y

        self.position.x += self.velocity.xspeed * self.speed_factor
        self.position.y += self.velocity.yspeed * self.speed_factor

        diff_x = self.position.x - self.position_history.x
        diff_y = self.position.y - self.position_history.y
        dist = math.sqrt(diff_x**2 + diff_y**2)

        # Steps to avoid 'phasing'
        steps = int(dist // GRID_SIZE) + 1
        for i in range(1, steps + 1):
            t = i / steps
            curr_x = self.position_history.x + diff_x * t
            curr_y = self.position_history.y + diff_y * t

            gx, gy = int(curr_x // GRID_SIZE), int(curr_y // GRID_SIZE)
            if (gx, gy) in self.context.collision_map:
                self.position.x, self.position.y = curr_x, curr_y
                self.destroy()
                return

        super().update()

    def draw(self) -> None:
        self.sprite.draw(Position(self.position.x + 2, self.position.y + 2))


class Saw(Hazard):
    position: Position
    position_history: Position
    REQUIRED = ("position",)

    def __init__(
        self,
        speed: float = 1.2,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.collision = CollisionRectangle(8, 4, 0, 4)
        self.sprite = Animation(sprite_name="Saw")
        self.velocity = Velocity(0, 0, 8, 0)
        self.speed = speed

    def is_at_solid(self, x: float, y: float) -> bool:
        left = (x + self.collision.offset_x) // GRID_SIZE
        right = (x + self.collision.offset_x + self.collision.width - 1) // GRID_SIZE
        top = (y + self.collision.offset_y) // GRID_SIZE

        for gx in [int(left), int(right)]:
            if (gx, int(top)) in self.context.collision_map:
                return True
        return False

    def post_init(self) -> None:
        self.position_history.x = self.position.x
        self.position_history.y = self.position.y

    def update(self) -> None:
        self.position_history.x = self.position.x

        if self.context.player:
            dx = self.context.player.position.x - self.position.x
            direction = 1.0 if dx > 0 else -1.0
            self.velocity.xspeed = pyxel.clamp(
                self.velocity.xspeed + direction * self.speed * self.speed_factor,
                -self.velocity.max_xspeed,
                self.velocity.max_xspeed,
            )

        move_amount = self.velocity.xspeed * self.speed_factor
        self.position.x += move_amount

        if self.is_at_solid(self.position.x, self.position.y):
            if move_amount > 0:
                right_edge = (
                    self.position.x + self.collision.offset_x + self.collision.width - 1
                )
                self.position.x = (
                    (right_edge // GRID_SIZE) * GRID_SIZE
                    - self.collision.width
                    - self.collision.offset_x
                )
            else:
                left_edge = self.position.x + self.collision.offset_x
                self.position.x = (
                    left_edge // GRID_SIZE + 1
                ) * GRID_SIZE - self.collision.offset_x

            self.velocity.xspeed = 0

        direction = self.position.x - self.position_history.x
        self.sprite.xscale = 1 if direction > 0 else -1
        super().update()
        self.sprite.update()

    def draw(self) -> None:
        self.sprite.draw(Position(self.position.x, self.position.y))
