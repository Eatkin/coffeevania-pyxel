from dataclasses import dataclass
from typing import Any
from typing import Dict
from typing import Literal

import pyxel

from coffeevania.components import Component
from coffeevania.components.position import Position
from coffeevania.game.graphics import GRID_SIZE
from coffeevania.game.graphics import SPRITE_DATA
from coffeevania.game.graphics import SpriteData


@dataclass
class Animation:
    sprite_name: str
    frame_duration: int = 6
    current_frame: int = 0
    timer: int = 0
    paused: bool = False
    xscale: Literal[-1, 1] = 1
    yscale: Literal[-1, 1] = 1

    def __post_init__(self) -> None:
        if self.sprite_name not in SPRITE_DATA:
            raise ValueError(
                f"Error: Requested sprite {self.sprite_name} but is not available in"
                " data"
            )

    @property
    def sprite_data(self) -> SpriteData:
        return SPRITE_DATA[self.sprite_name]

    @property
    def animation_length(self) -> int:
        return self.sprite_data.width // GRID_SIZE

    def update(self) -> None:
        if self.paused:
            return

        self.timer += 1
        if self.timer >= self.frame_duration:
            self.timer = 0
            self.current_frame = (self.current_frame + 1) % self.animation_length

    def draw(self, position: Position) -> None:
        bank = self.sprite_data.bank
        x = self.sprite_data.x + self.current_frame * GRID_SIZE
        y = self.sprite_data.y
        pyxel.blt(
            position.x,
            position.y,
            bank,
            x,
            y,
            GRID_SIZE * self.xscale,
            GRID_SIZE * self.yscale,
            0,
        )


class Animator(Component):
    def __init__(
        self, animation_data: Dict[Any, str], starting_state: Any, **kwargs: Any
    ) -> None:
        self.animation_data = animation_data
        self.animation = Animation(self.animation_data[starting_state], **kwargs)
        self.current_state = starting_state

    def update(self, state: Any) -> None:
        if state in self.animation_data and self.current_state != state:
            self.animation.sprite_name = self.animation_data[state]
            self.animation.current_frame = 0
            self.animation.timer = 0
            self.current_state = state
        self.animation.update()

    def draw(self, position: Position) -> None:
        self.animation.draw(position)

    def face(self, direction: Literal[-1, 1]) -> None:
        self.animation.xscale = direction

    def face_towards(self, hinput: float) -> None:
        if hinput != 0:
            self.animation.xscale = 1 if hinput > 0 else -1

    def pause(self) -> None:
        self.animation.paused = True

    def resume(self) -> None:
        self.animation.paused = False

    def set_speed(self, frame_duration: int) -> None:
        self.animation.frame_duration = frame_duration

    def reset(self) -> None:
        self.animation.current_frame = 0
        self.animation.timer = 0
