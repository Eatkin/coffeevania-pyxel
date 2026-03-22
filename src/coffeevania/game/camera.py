from typing import Tuple

import pyxel

from coffeevania.common.game import GAME_HEIGHT
from coffeevania.common.game import GAME_WIDTH
from coffeevania.game_objects.basic import Player
from coffeevania.utils import lerp


class Camera:
    def __init__(self, following: Player, padding: Tuple[int, int]) -> None:
        if not hasattr(following, "position"):
            raise AttributeError(
                "Entity camera follows must have position component."
                f" {following.__class__.__name__} has no position component"
            )
        self.following = following
        self.camera_x = following.position.x - GAME_WIDTH // 2
        self.camera_y = following.position.y - GAME_HEIGHT // 2
        self.padding = padding

    def update(self) -> None:
        # World space position of player relative to camera
        screen_x = self.following.position.x - self.camera_x
        screen_y = self.following.position.y - self.camera_y

        px, py = self.padding

        # Only move camera if player outside deadzone
        if screen_x < px:
            self.camera_x = lerp(self.camera_x, self.following.position.x - px, 0.2)
        elif screen_x > GAME_WIDTH - px:
            self.camera_x = lerp(
                self.camera_x, self.following.position.x - (GAME_WIDTH - px), 0.2
            )

        if screen_y < py:
            self.camera_y = lerp(self.camera_y, self.following.position.y - py, 0.2)
        elif screen_y > GAME_HEIGHT - py:
            self.camera_y = lerp(
                self.camera_y, self.following.position.y - (GAME_HEIGHT - py), 0.2
            )

        pyxel.camera(self.camera_x, self.camera_y)

    def reset(self) -> None:
        pyxel.camera(0, 0)
