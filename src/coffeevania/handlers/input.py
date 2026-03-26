from enum import Enum
from enum import auto

import pyxel


class Action(Enum):
    MOVE_LEFT = auto()
    MOVE_RIGHT = auto()
    MOVE_UP = auto()
    MOVE_DOWN = auto()
    JUMP = auto()
    DEBUG_DILATE = auto()
    MODIFY = auto()


class InputHandler:
    def __init__(self) -> None:
        self.bindings = {
            Action.MOVE_LEFT: [pyxel.KEY_LEFT, pyxel.KEY_H],
            Action.MOVE_RIGHT: [pyxel.KEY_RIGHT, pyxel.KEY_L],
            Action.MOVE_UP: [pyxel.KEY_UP, pyxel.KEY_K],
            Action.MOVE_DOWN: [pyxel.KEY_DOWN, pyxel.KEY_J],
            Action.JUMP: [pyxel.KEY_Z, pyxel.KEY_K],
            Action.DEBUG_DILATE: [pyxel.KEY_T],
            Action.MODIFY: [pyxel.KEY_SHIFT],
        }

    def held(self, action: Action) -> bool:
        return bool(any(pyxel.btn(b) for b in self.bindings[action]))

    def pressed(self, action: Action) -> bool:
        return bool(any(pyxel.btnp(b) for b in self.bindings[action]))

    @property
    def hinput(self) -> int:
        return self.held(Action.MOVE_RIGHT) - self.held(Action.MOVE_LEFT)

    @property
    def vinput(self) -> int:
        return self.held(Action.MOVE_DOWN) - self.held(Action.MOVE_UP)

    @property
    def jump(self) -> bool:
        return self.pressed(Action.JUMP)
