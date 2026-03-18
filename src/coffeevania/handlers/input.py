from enum import Enum
from enum import auto

import pyxel


class Action(Enum):
    MOVE_LEFT = auto()
    MOVE_RIGHT = auto()
    MOVE_UP = auto()
    MOVE_DOWN = auto()
    JUMP = auto()


class InputHandler:
    def __init__(self) -> None:
        self.bindings = {
            Action.MOVE_LEFT: pyxel.KEY_LEFT,
            Action.MOVE_RIGHT: pyxel.KEY_RIGHT,
            Action.MOVE_UP: pyxel.KEY_UP,
            Action.MOVE_DOWN: pyxel.KEY_DOWN,
            Action.JUMP: pyxel.KEY_Z,
        }

    def held(self, action: Action) -> bool:
        return bool(pyxel.btn(self.bindings[action]))

    def pressed(self, action: Action) -> bool:
        return bool(pyxel.btnp(self.bindings[action]))

    @property
    def hinput(self) -> int:
        return self.held(Action.MOVE_RIGHT) - self.held(Action.MOVE_LEFT)

    @property
    def vinput(self) -> int:
        return self.held(Action.MOVE_DOWN) - self.held(Action.MOVE_UP)

    @property
    def jump(self) -> bool:
        return self.pressed(Action.JUMP)
