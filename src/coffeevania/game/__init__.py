from typing import Any
from typing import List
from typing import Type

import pyxel

from coffeevania.common.context import GlobalContext
from coffeevania.common.game import GAME_HEIGHT
from coffeevania.common.game import GAME_WIDTH
from coffeevania.game_objects.basic import CoffeevaniaEntity


class App:
    def __init__(self, game_width: int = GAME_WIDTH, game_height: int = GAME_HEIGHT) -> None:
        pyxel.init(game_width, game_height)
        self.entities: List[CoffeevaniaEntity] = []
        self.context = GlobalContext(app=self)

    def update(self) -> None:
        for e in self.entities:
            e.update()

    def draw(self) -> None:
        pyxel.cls(0)
        for e in self.entities:
            e.draw()

    def run(self) -> None:
        pyxel.run(self.update, self.draw)

    def create_entity(
        self, entity_cls: Type[CoffeevaniaEntity], *args: Any, **kwargs: Any
    ) -> CoffeevaniaEntity:
        """Factory function to create entities"""
        entity = entity_cls(context=self.context, *args, **kwargs)  # type: ignore
        self.entities.append(entity)
        return entity
