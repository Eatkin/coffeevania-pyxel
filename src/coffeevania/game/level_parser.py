import csv
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional

from coffeevania.common import ASSETS_PATH
from coffeevania.common.context import GlobalContext
from coffeevania.components.position import Position
from coffeevania.game.graphics import GRID_SIZE
from coffeevania.game_objects.basic import Block
from coffeevania.game_objects.basic import Coffee
from coffeevania.game_objects.basic import CoffeevaniaEntity
from coffeevania.game_objects.basic import Player
from coffeevania.game_objects.hazards import Saw
from coffeevania.game_objects.hazards import Spike
from coffeevania.game_objects.hazards import VerticalShooter

LEVELS_PATH = ASSETS_PATH / "levels"


def get_legend(
    context: GlobalContext,
) -> Dict[str, Optional[Callable[[float, float], CoffeevaniaEntity]]]:
    return {
        "P": lambda x, y: context.app.create_entity(Player, position=Position(x, y)),
        "#": lambda x, y: context.app.create_entity(Block, position=Position(x, y)),
        "C": lambda x, y: context.app.create_entity(Coffee, position=Position(x, y)),
        "s": lambda x, y: context.app.create_entity(Spike, position=Position(x, y)),
        "x": lambda x, y: context.app.create_entity(Saw, position=Position(x, y)),
        "V": lambda x, y: context.app.create_entity(
            VerticalShooter, position=Position(x, y)
        ),
        ".": None,
    }


def load_level(name: str, offset_x: int, offset_y: int, context: GlobalContext, block_queue: List[Position]) -> None:
    path = LEVELS_PATH / f"{name}.txt"
    if not path.exists():
        raise FileNotFoundError(f"Level '{name}' not found at {path}")
    legend = get_legend(context)
    with open(path, "r") as f:
        for y, line in enumerate(f):
            stripped = line.strip()
            if not stripped:
                continue  # skip blank lines
            for x, char in enumerate(stripped):
                if char in legend and legend[char]:
                    if char == "#":
                        block_queue.append(Position(x * GRID_SIZE + offset_x, y * GRID_SIZE + offset_y))
                    else:
                        legend[char](x * GRID_SIZE + offset_x, y * GRID_SIZE + offset_y)  # type: ignore


def load_world(context: GlobalContext) -> None:
    path = LEVELS_PATH / "layout.csv"
    layout: List[List[str]] = []

    # Use this queue to ensure correct instance creation order
    # Basically blocks on top of everything else
    block_queue: List[Position] = []

    with open(path, "r") as c:
        reader = csv.reader(c)
        layout = list(reader)

    # NOTE: All chunks should be same height
    # Can make new tools to edit larger chunks in future etc
    chunk_width, chunk_height = 45, 12
    x_offset, y_offset = 0, 0

    for row in layout:
        # Reset x_offset every new row
        x_offset = 0
        for chunk in row:
            if chunk:
                load_level(chunk, x_offset, y_offset, context, block_queue)
            x_offset += chunk_width * GRID_SIZE
        y_offset += chunk_height * GRID_SIZE

    # Create all the blocks
    legend = get_legend(context)
    for p in block_queue:
        legend["#"](p.x, p.y) # type: ignore


    context.app.post_level_create()
