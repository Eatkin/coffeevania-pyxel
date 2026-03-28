from typing import Any
from typing import Dict
from typing import Optional
from typing import Tuple

import pyxel

from coffeevania.common.context import GlobalContext
from coffeevania.common.game import GAME_HEIGHT
from coffeevania.common.game import GAME_WIDTH
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
    position: Position
    REQUIRED: Tuple[str, ...] = ()

    def __init__(self, context: GlobalContext, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.context = context
        for component in self.REQUIRED:
            if not hasattr(self, component):
                raise RuntimeError(
                    f"{self.__class__.__name__} missing required component: {component}"
                )

        context.app.entities.add(self)

    def is_on_screen(self) -> bool:
        camera = self.context.app.camera
        if not camera:
            return True
        cx, cy = camera.camera_x, camera.camera_y
        return (
            self.position.x < cx + GAME_WIDTH + GRID_SIZE
            and self.position.x > cx - GRID_SIZE
            and self.position.y < cy + GAME_HEIGHT + GRID_SIZE
            and self.position.y > cy - GRID_SIZE
        )

    @property
    def debug(self) -> bool:
        return self.context.debug

    @property
    def speed_factor(self) -> float:
        return 1 / self.context.time_dilation

    def destroy(self) -> None:
        self.context.app.entities.remove(self)
        del self


class Collectible(CoffeevaniaEntity):
    """Container class"""

    collision: CollisionRectangle

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # We add ourselves to collidables
        super().__init__(*args, **kwargs)
        self.context.collidables.add(self)

    def destroy(self) -> None:
        self.context.app.entities.remove(self)
        self.context.collidables.remove(self)
        del self


class PlayerGhost(CoffeevaniaEntity):
    position: Position
    REQUIRED = ("position",)

    def __init__(
        self,
        animation_data: Dict[CatState, str],
        current_state: CatState,
        current_frame: int,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.animator = Animator(
            animation_data=animation_data,
            starting_state=current_state,
            frame_duration=999,
        )
        self.animator.animation.current_frame = current_frame

        self.life = 0.5
        self.decay_rate = 0.1 * self.speed_factor

    def update(self) -> None:
        self.life -= self.decay_rate
        if self.life <= 0:
            self.destroy()

    def draw(self) -> None:
        pyxel.dither(self.life)
        self.animator.draw(self.position)
        pyxel.dither(1.0)


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
        self.time_in_air = 0
        self.coyote_time_allowed = 10
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

    def is_at_solid(self, x: float, y: float) -> bool:
        left = (x + self.collision.offset_x) // GRID_SIZE
        right = (x + self.collision.offset_x + self.collision.width - 1) // GRID_SIZE
        top = (y + self.collision.offset_y) // GRID_SIZE
        bottom = (y + self.collision.offset_y + self.collision.height - 1) // GRID_SIZE

        for gx in [int(left), int(right)]:
            for gy in [int(top), int(bottom)]:
                if (gx, gy) in self.context.collision_map:
                    return True
        return False

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
        if self.velocity.xspeed != 0:
            self.position.x += self.velocity.xspeed

            if self.is_at_solid(self.position.x, self.position.y):
                if self.velocity.xspeed > 0:
                    right_edge = (
                        self.position.x
                        + self.collision.offset_x
                        + self.collision.width
                        - 1
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

        # Y axis
        if self.velocity.yspeed != 0:
            self.position.y += self.velocity.yspeed

            if self.is_at_solid(self.position.x, self.position.y):
                if self.velocity.yspeed > 0:
                    foot_pos = (
                        self.position.y
                        + self.collision.offset_y
                        + self.collision.height
                        - 1
                    )
                    self.position.y = (
                        (foot_pos // GRID_SIZE) * GRID_SIZE
                        - self.collision.height
                        - self.collision.offset_y
                    )
                else:
                    head_pos = self.position.y + self.collision.offset_y
                    self.position.y = (
                        head_pos // GRID_SIZE + 1
                    ) * GRID_SIZE - self.collision.offset_y

                self.velocity.yspeed = 0

        # Coyote time handler
        if self._is_grounded():
            self.time_in_air = 0
        else:
            self.time_in_air += 1

        # Jump + gravity
        # Hold jump for higher jump
        if (
            self.context.input_handler.jump
            and self.time_in_air < self.coyote_time_allowed
        ):
            self.velocity.yspeed = -self.jump_force

        # Acceleration due to gravity
        # Modifications: Lower gravity if jump held, higher gravity if jump tapped
        base_grav = self.context.gravity
        if self.context.input_handler.held(Action.JUMP):
            base_grav *= 0.6
        elif self.time_in_air < 15:
            base_grav *= 1.5

        if not self._is_grounded():
            self.velocity.yspeed = clamp(
                self.velocity.yspeed
                + base_grav,
                -self.velocity.max_yspeed,
                self.velocity.max_yspeed,
            )

        # Check if collided with stuff
        for e in list(self.context.collidables):
            if isinstance(e, Coffee) and overlaps(self, e):
                self.context.time_dilation *= 2
                e.destroy()
            elif isinstance(e, Checkpoint) and overlaps(self, e):
                self.checkpoint_pos.x = e.position_start.x
                self.checkpoint_pos.y = e.position_start.y

        if self.debug:
            self._debug_controls()

        self._update_state()
        self.animator.update(self.state)
        self.animator.face_towards(hinput)

        # Create our ghost - eh not sure I like it
        # if pyxel.frame_count % 30 == 0:
        #     self.context.app.create_entity(
        #         PlayerGhost,
        #         position=Position(self.position.x, self.position.y),
        #         animation_data=self.animator.animation_data,
        #         current_state=self.state,
        #         current_frame=self.animator.animation.current_frame,
        #     )

    def draw(self) -> None:
        self.animator.draw(position=self.position)
        if self.debug:
            self._debug_draw()

    def die(self) -> None:
        # Go back to checkpoint!
        self.position.x = self.checkpoint_pos.x
        self.position.y = self.checkpoint_pos.y

    def _is_grounded(self) -> bool:
        return self.is_at_solid(self.position.x, self.position.y + 1)

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
            if self.context.input_handler.pressed(Action.MODIFY):
                self.context.time_dilation //= 2
            else:
                self.context.time_dilation *= 2

    def _debug_draw(self) -> None:
        pyxel.text(
            self.position.x + 8,
            self.position.y,
            str(self.context.time_dilation),
            3,
        )


class Block(CoffeevaniaEntity):
    position: Position
    REQUIRED = ("position",)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.collision = CollisionRectangle(8, 8, solid=True)
        self.sprite_resource = SPRITE_DATA["GrassTiles"]
        self.sprite_draw_offset = 0

    def post_init(self) -> None:
        gx, gy = int(self.position.x // GRID_SIZE), int(self.position.y // GRID_SIZE)
        bits = 0

        # Neighbor relative offsets: (dx, dy, bit_value)
        # North=1, East=2, South=4, West=8
        neighbors = [
            (0, -1, 1),  # N
            (1, 0, 2),  # E
            (0, 1, 4),  # S
            (-1, 0, 8),  # W
        ]

        for dx, dy, bit in neighbors:
            if (gx + dx, gy + dy) in self.context.collision_map:
                bits |= bit

        self.sprite_draw_offset = GRID_SIZE * bits

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


class Coffee(Collectible):
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
        self.offset_timer_max = 180.0

    def update(self) -> None:
        self.offset_timer += 1 * self.speed_factor
        self.offset = self.offset_max * pyxel.sin(
            360 * self.offset_timer / self.offset_timer_max
        )

        if self.offset_timer >= self.offset_timer_max:
            self.offset_timer = 0

    def draw(self) -> None:
        self.sprite.draw(Position(self.position.x, self.position.y + self.offset))


class Checkpoint(Collectible):
    position: Position
    position_start: Position
    collision: CollisionRectangle
    REQUIRED = ("position",)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.collision = CollisionRectangle(8, 8, solid=False)

    def post_init(self) -> None:
        self.position_start = Position(self.position.x, self.position.y)
        gx = int(self.position.x // GRID_SIZE)
        gy = int(self.position.y // GRID_SIZE)

        current_gy = gy
        while current_gy >= 0:
            if (gx, current_gy) in self.context.collision_map:
                break
            current_gy -= 1

        ceiling_y = (current_gy + 1) * GRID_SIZE
        beam_height = self.position.y - ceiling_y
        self.position.y = ceiling_y
        self.collision.height = beam_height + GRID_SIZE

    def draw(self) -> None:
        pyxel.circ(
            self.position_start.x + 4, self.position_start.y + 4, 4, pyxel.COLOR_PEACH
        )
