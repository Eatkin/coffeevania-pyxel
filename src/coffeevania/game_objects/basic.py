from typing import Any, List
from typing import Optional
from typing import Tuple

import pyxel

from coffeevania.common.context import GlobalContext
from coffeevania.components import Component
from coffeevania.components.collision import CollisionRectangle
from coffeevania.components.common import REQUIRED_COMPONENTS
from coffeevania.components.position import Position
from coffeevania.components.velocity import Velocity
from coffeevania.utils import Collidable, clamp
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


class Player(CoffeevaniaEntity):
    position: Position
    REQUIRED = ("position",)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.collision = CollisionRectangle(8, 8)
        self.velocity = Velocity(max_xspeed=2, max_yspeed=8)
        self.jump_force = 8

    @property
    def blocks(self) -> List[Collidable]:
        return [e for e in self.context.collidables if e is not self]

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
            self.position.x -= hinput
            step = 1 if hinput > 0 else -1
            while not any(overlaps(self, b) for b in self.blocks):
                self.position.x += step
            self.position.x -= step

        # Y axis
        self.position.y += self.velocity.yspeed
        if any(overlaps(self, b) for b in self.blocks):
            self.position.y -= self.velocity.yspeed
            step = 1 if self.velocity.yspeed > 0 else -1
            while not any(overlaps(self, b) for b in self.blocks):
                self.position.y += step
            self.position.y -= step
            self.velocity.yspeed = 0

        # Jump + gravity
        # TODO: Hold jump to jump higher / don't hold to jump lower
        if self.context.input_handler.jump and self._is_grounded():
            self.velocity.yspeed = -self.jump_force

        # Acceleration due to gravity
        self.velocity.yspeed = clamp(
            self.velocity.yspeed + self.context.gravity,
            -self.velocity.max_yspeed,
            self.velocity.max_yspeed,
        )

    def draw(self) -> None:
        pyxel.rect(self.position.x, self.position.y, 8, 8, 9)

    def _is_grounded(self) -> bool:
        self.position.y += 1
        grounded = any(overlaps(self, b) for b in self.blocks)
        self.position.y -= 1
        return bool(grounded)


class Block(CoffeevaniaEntity):
    position: Position
    collision: CollisionRectangle
    REQUIRED = ("position",)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.collision = CollisionRectangle(8, 8)

    def draw(self) -> None:
        pyxel.rect(self.position.x, self.position.y, 8, 8, 1)
