from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from typing import TYPE_CHECKING
from typing import Optional
from typing import Set

from coffeevania.common.types import CollisionMapType
from coffeevania.handlers.input import InputHandler

if TYPE_CHECKING:
    from coffeevania.game import App
    from coffeevania.game_objects.basic import Collectible
    from coffeevania.game_objects.basic import Player


@dataclass
class GlobalContext:
    app: App
    collidables: Set[Collectible] = field(default_factory=set)
    collision_map: CollisionMapType = field(default_factory=dict)
    input_handler: InputHandler = field(default_factory=InputHandler)
    time_dilation: float = 1.0
    gravity: float = 0.4
    debug: bool = True
    player: Optional["Player"] = None
