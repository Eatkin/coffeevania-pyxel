from pathlib import Path
from typing import Any, Set
from typing import Optional
from typing import Type

import pyxel

from coffeevania.common.context import GlobalContext
from coffeevania.common.game import CAMERA_PADDING_X
from coffeevania.common.game import CAMERA_PADDING_Y
from coffeevania.common.game import GAME_HEIGHT
from coffeevania.common.game import GAME_WIDTH
from coffeevania.game.camera import Camera
from coffeevania.game.level_parser import load_world
from coffeevania.game_objects.basic import CoffeevaniaEntity
from coffeevania.game_objects.basic import Player

BASE_DIR = Path(__file__).parent.parent.parent.parent


class App:
    def __init__(
        self, game_width: int = GAME_WIDTH, game_height: int = GAME_HEIGHT
    ) -> None:
        pyxel.init(game_width, game_height, fps=60)
        self.entities: Set[CoffeevaniaEntity] = set()
        self.context = GlobalContext(app=self)

        self.camera: Optional[Camera] = None

        block_map = load_world(self.context)
        self.context.collision_map = block_map

        self.post_level_create()

        # Find player
        try:
            player = next(e for e in self.entities if isinstance(e, Player))
            self.context.player = player
        except StopIteration:
            raise RuntimeError(
                "World loaded with no available player object - add player to the"
                " game!!"
            )
        self.run(player)

    def update(self) -> None:
        for e in list(self.entities):
            e.update()

        self.camera.update()  # type: ignore

    def draw(self) -> None:
        pyxel.cls(pyxel.COLOR_DARK_BLUE)
        for e in self.entities:
            if e.is_on_screen():
                e.draw()

        self.camera.reset()  # type: ignore

        for e in self.entities:
            e.draw_hud()

        if self.context.debug:
            pyxel.text(2, 2, "DEBUG BUILD", 3)

    def run(self, player_inst: Player) -> None:
        self.camera = Camera(player_inst, (CAMERA_PADDING_X, CAMERA_PADDING_Y))
        pyxel.run(self.update, self.draw)

    def create_entity(
        self, entity_cls: Type[CoffeevaniaEntity], *args: Any, **kwargs: Any
    ) -> CoffeevaniaEntity:
        """Factory function to create entities"""
        entity = entity_cls(context=self.context, *args, **kwargs)  # type: ignore
        return entity

    def post_level_create(self) -> None:
        for entity in self.entities:
            entity.post_init()
