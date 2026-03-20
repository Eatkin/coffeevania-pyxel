from typing import Any
from typing import List
from typing import Optional
from typing import Tuple

import pyxel

from coffeevania.common.context import GlobalContext
from coffeevania.components import Component
from coffeevania.components.animation import Animator
from coffeevania.components.collision import CollisionRectangle
from coffeevania.components.common import REQUIRED_COMPONENTS
from coffeevania.components.position import Position
from coffeevania.components.velocity import Velocity
from coffeevania.game.graphics import Sprite
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

    def update(self) -> None:
        pass

    def draw(self) -> None:
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


class Player(CoffeevaniaEntity):
    position: Position
    REQUIRED = ("position",)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.collision = CollisionRectangle(8, 8)
        self.velocity = Velocity(max_xspeed=2, max_yspeed=8)
        self.jump_force = 8
        self.animator = Animator(
            sprites={
                CatState.IDLE: Sprite(bank=0, src_x=0, src_y=0, frame_count=7),
            }
        )
        self.state = CatState.IDLE

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

        if self.debug:
            self.debug_controls()

        self._update_state()

    def draw(self) -> None:
        # OVERRIDE BECAUSE ONLY IDLE EXISTS
        # TODO: Update state
        self.animator.draw(state=CatState.IDLE, position=self.position)
        if self.debug:
            pyxel.text(
                self.position.x + 8,
                self.position.y,
                f"x: {self.position.x:.2f}, y: {self.position.y:.2f}",
                3,
            )

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

        # OVERRIDE BECAUSE ONLY IDLE EXISTS
        # TODO: REMOVE
        self.animator.update(CatState.IDLE)

    def debug_controls(self) -> None:
        if self.context.input_handler.pressed(Action.DEBUG_DILATE):
            self.context.time_dilation *= 2


class Block(CoffeevaniaEntity):
    position: Position
    collision: CollisionRectangle
    REQUIRED = ("position",)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.collision = CollisionRectangle(8, 8, solid=True)

    def draw(self) -> None:
        pyxel.rect(self.position.x, self.position.y, 8, 8, 1)
