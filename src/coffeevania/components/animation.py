from dataclasses import dataclass, field
from typing import Dict

import pyxel

from coffeevania.components import Component
from coffeevania.components.position import Position
from coffeevania.game.graphics import Sprite
from coffeevania.game.states import CatState


@dataclass
class Animator(Component):
    sprites: Dict[CatState, Sprite] = field(default_factory=dict)
    current_frame: int = 0
    timer: int = 0

    def update(self, state: CatState) -> None:
        sprite = self.sprites[state]
        self.timer += 1
        if self.timer >= sprite.frame_duration:
            self.timer = 0
            self.current_frame = (self.current_frame + 1) % sprite.frame_count

    def get_source_x(self, state: CatState) -> int:
        sprite = self.sprites[state]
        return self.current_frame * sprite.width

    def draw(self, state: CatState, position: Position) -> None:
        sprite = self.sprites[state]
        frame_x = sprite.src_x + self.get_source_x(state)
        pyxel.blt(position.x, position.y, 0, frame_x, sprite.src_y, sprite.width, sprite.height, 0)
