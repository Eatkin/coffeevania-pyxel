from coffeevania.common import ASSETS_PATH
from coffeevania.common.context import GlobalContext
from coffeevania.components.position import Position
from coffeevania.game.graphics import GRID_SIZE
from coffeevania.game_objects.basic import Block, Coffee
from coffeevania.game_objects.basic import Player
from coffeevania.game_objects.hazards import BouncingHazard

LEVELS_PATH = ASSETS_PATH / "levels"


def get_legend(context: GlobalContext) -> dict:
    return {
        "P": lambda x, y: context.app.create_entity(Player, position=Position(x, y)),
        "#": lambda x, y: context.app.create_entity(Block, position=Position(x, y)),
        "C": lambda x, y: context.app.create_entity(Coffee, position=Position(x, y)),
        "B": lambda x, y: context.app.create_entity(BouncingHazard, position=Position(x, y)),
        ".": None,
    }


def load_level(name: str, context: GlobalContext) -> None:
    path = LEVELS_PATH / f"{name}.txt"
    if not path.exists():
        raise FileNotFoundError(f"Level '{name}' not found at {path}")
    legend = get_legend(context)
    with open(path, "r") as f:
        for y, line in enumerate(f):
            for x, char in enumerate(line.strip()):
                if char in legend and legend[char]:
                    legend[char](x * GRID_SIZE, y * GRID_SIZE)
