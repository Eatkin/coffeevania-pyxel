from typing import Any
from typing import List
from typing import Optional
from typing import Tuple
from typing import Type

import pyxel

from coffeevania.common.context import GlobalContext
from coffeevania.components import Component
from coffeevania.components.collision import CollisionRectangle
from coffeevania.components.common import REQUIRED_COMPONENTS
from coffeevania.components.position import Position
from coffeevania.components.sprites import Animator
from coffeevania.components.sprites import StaticSprite
from coffeevania.components.velocity import Velocity
from coffeevania.game.graphics import GRID_SIZE
from coffeevania.game.graphics import SPRITE_DATA
from coffeevania.game.graphics import TRANSPARENT_COLOUR
from coffeevania.game.states import CatState
from coffeevania.handlers.input import Action
from coffeevania.utils import Collidable
from coffeevania.utils import clamp
from coffeevania.utils import lerp
from coffeevania.utils import overlaps


class Entity:
    def __init__(self, **components: Optional[Component]) -> None:
        for name, component in components.items():
            if component is not None:
                setattr(self, name, component)

        # Add required components
        for c, cls in REQUIRED_COMPONENTS.items():
            if not hasattr(self, c):
                component = cls()
                setattr(self, c, component)

    def post_init(self) -> None:
        pass

    def update(self) -> None:
        pass

    def draw(self) -> None:
        pass

    def draw_hud(self) -> None:
        pass

    def destroy(self) -> None:
        pass


class CoffeevaniaEntity(Entity):
    REQUIRED: Tuple[str, ...] = ()

    def __init__(self, context: GlobalContext, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.context = context
        for component in self.REQUIRED:
            if not hasattr(self, component):
                raise RuntimeError(
                    f"{self.__class__.__name__} missing required component: {component}"
                )

    @property
    def debug(self) -> bool:
        return self.context.debug

    @property
    def speed_factor(self) -> float:
        return 1 / self.context.time_dilation

    def destroy(self) -> None:
        self.context.destroy_entity(self)
        del self


class Player(CoffeevaniaEntity):
    position: Position
    REQUIRED = ("position",)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.collision = CollisionRectangle(6, 7, 1, 1)
        # Hurtbox used for collision
        self.hurtbox = CollisionRectangle(4, 4, 2, 2)
        self.velocity = Velocity(max_xspeed=1, max_yspeed=4)
        self.jump_force = 4
        self.state = CatState.IDLE
        animation_data = {
            CatState.IDLE: "PlayerIdle",
            CatState.RUNNING: "PlayerMove",
            CatState.JUMPING: "PlayerJump",
            CatState.FALLING: "PlayerFall",
        }
        self.animator = Animator(
            animation_data=animation_data, starting_state=self.state, frame_duration=8
        )

        # Copy start position for checkpoint
        self.checkpoint_pos = Position(self.position.x, self.position.y)

    @property
    def blocks(self) -> List[Collidable]:
        return [
            e for e in self.context.collidables if e is not self and e.collision.solid
        ]

    def update(self) -> None:
        hinput = self.context.input_handler.hinput

        target_xspeed = hinput * self.velocity.max_xspeed
        # TODO: Possibly use easing? Lerp seems 'jumpy'
        self.velocity.xspeed = clamp(
            lerp(self.velocity.xspeed, target_xspeed, 0.3, epsilon=0.01),
            -self.velocity.max_xspeed,
            self.velocity.max_xspeed,
        )

        # X axis
        self.position.x += self.velocity.xspeed
        if any(overlaps(self, b) for b in self.blocks):
            self.position.x -= self.velocity.xspeed
            step = 1 if self.velocity.xspeed > 0 else -1
            while not any(overlaps(self, b) for b in self.blocks):
                self.position.x += step
            self.position.x -= step
            self.velocity.xspeed = 0
            # Round in the direction of step
            self.position.x = (
                pyxel.floor(self.position.x)
                if step == -1
                else pyxel.ceil(self.position.x)
            )

        # Y axis - hold jump for lower gravity i.e. higher jump
        self.position.y += self.velocity.yspeed
        if any(overlaps(self, b) for b in self.blocks):
            self.position.y -= self.velocity.yspeed
            step = 1 if self.velocity.yspeed > 0 else -1
            while not any(overlaps(self, b) for b in self.blocks):
                self.position.y += step
            self.position.y -= step
            self.velocity.yspeed = 0
            # Round in the direction of step
            self.position.y = (
                pyxel.floor(self.position.y)
                if step == -1
                else pyxel.ceil(self.position.y)
            )

        # Jump + gravity
        if self.context.input_handler.jump and self._is_grounded():
            self.velocity.yspeed = -self.jump_force

        # Acceleration due to gravity
        # Allow holding jump to lessen effects of gravity
        self.velocity.yspeed = clamp(
            self.velocity.yspeed
            + self.context.gravity
            * (1 - 0.4 * self.context.input_handler.held(Action.JUMP)),
            -self.velocity.max_yspeed,
            self.velocity.max_yspeed,
        )

        # Check if collided with coffee
        coffee = self.place_meeting(Coffee)
        if coffee:
            self.context.time_dilation *= 2
            coffee.destroy()

        if self.debug:
            self._debug_controls()

        self._update_state()
        self.animator.update(self.state)
        self.animator.face_towards(hinput)

    def draw(self) -> None:
        self.animator.draw(position=self.position)
        if self.debug:
            self._debug_draw()

    def place_meeting(self, other: Type[Collidable]) -> Optional[Collidable]:
        for e in self.context.collidables:
            if isinstance(e, other):
                if overlaps(self, e):
                    return e

        return None

    def die(self) -> None:
        # Go back to checkpoint!
        self.position.x = self.checkpoint_pos.x
        self.position.y = self.checkpoint_pos.y

    def _is_grounded(self) -> bool:
        self.position.y += 1
        grounded = any(overlaps(self, b) for b in self.blocks)
        self.position.y -= 1
        return bool(grounded)

    def _update_state(self) -> None:
        if not self._is_grounded():
            self.state = (
                CatState.JUMPING if self.velocity.yspeed < 0 else CatState.FALLING
            )
        elif abs(self.velocity.xspeed) > 0.1:
            self.state = CatState.RUNNING
        else:
            self.state = CatState.IDLE

    def _debug_controls(self) -> None:
        if self.context.input_handler.pressed(Action.DEBUG_DILATE):
            self.context.time_dilation *= 2

    def _debug_draw(self) -> None:
        pyxel.text(
            self.position.x + 8,
            self.position.y,
            str(self.context.time_dilation),
            3,
        )
        x = self.position.x + self.hurtbox.offset_x
        y = self.position.y + self.hurtbox.offset_y
        w = self.hurtbox.width
        h = self.hurtbox.height

        # pyxel.rect(x, y, w, h, pyxel.COLOR_RED)


class Block(CoffeevaniaEntity):
    position: Position
    collision: CollisionRectangle
    REQUIRED = ("position",)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.collision = CollisionRectangle(8, 8, solid=True)
        self.sprite_resource = SPRITE_DATA["GrassTiles"]
        self.sprite_draw_offset = 0

    def post_init(self) -> None:
        x, y = self.position.x, self.position.y
        bits = 0
        
        checks = [
            (0, -GRID_SIZE, 1),   # N = 1
            (GRID_SIZE, 0, 2),    # E = 2
            (0, GRID_SIZE, 4),    # S = 4
            (-GRID_SIZE, 0, 8),   # W = 8
        ]
        
        for dx, dy, bit in checks:
            self.position.x = x + dx
            self.position.y = y + dy
            if self.place_meeting(Block):
                bits |= bit
        
        self.position.x = x
        self.position.y = y
        self.sprite_draw_offset = GRID_SIZE * bits

    def place_meeting(self, other: Type[Collidable]) -> Optional[Collidable]:
        for e in self.context.collidables:
            if isinstance(e, other) and e is not self:
                if overlaps(self, e):
                    return e

        return None

    def draw(self) -> None:
        pyxel.blt(
            self.position.x,
            self.position.y,
            self.sprite_resource.bank,
            self.sprite_resource.x + self.sprite_draw_offset,
            self.sprite_resource.y,
            GRID_SIZE,
            GRID_SIZE,
            TRANSPARENT_COLOUR,
        )


class Coffee(CoffeevaniaEntity):
    position: Position
    collision: CollisionRectangle
    REQUIRED = ("position",)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.sprite = StaticSprite("Coffee")
        self.collision = CollisionRectangle(8, 8, solid=False)

        # Bob up and down
        self.offset = 0.0
        self.offset_max = 3.0
        self.offset_timer = 0.0
        self.offset_timer_max = 120.0

    def update(self) -> None:
        self.offset_timer += 1 * self.speed_factor
        self.offset = self.offset_max * pyxel.sin(
            360 * self.offset_timer / self.offset_timer_max
        )

        if self.offset_timer >= self.offset_timer_max:
            self.offset_timer = 0

    def draw(self) -> None:
        self.sprite.draw(Position(self.position.x, self.position.y + self.offset))
