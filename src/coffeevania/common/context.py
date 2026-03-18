from dataclasses import dataclass
from dataclasses import field
from typing import TYPE_CHECKING
from typing import List
from typing import cast

from coffeevania.handlers.input import InputHandler
from coffeevania.utils import Collidable

if TYPE_CHECKING:
    from coffeevania.game import App
    from coffeevania.game_objects.basic import CoffeevaniaEntity


@dataclass
class GlobalContext:
    app: "App"
    time_dilation: int = 1
    input_handler: InputHandler = field(default_factory=InputHandler)
    gravity: float = 1.4
    debug: bool = True

    @property
    def entity_list(self) -> List["CoffeevaniaEntity"]:
        return self.app.entities

    @property
    def collidables(self) -> List[Collidable]:
        return cast(
            List[Collidable], [e for e in self.entity_list if hasattr(e, "collision")]
        )
