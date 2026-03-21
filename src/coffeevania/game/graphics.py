from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict

import pyxel

from coffeevania.common import ASSETS_PATH

SPRITE_DATA: Dict[str, SpriteData] = {}
GRID_SIZE = 8

@dataclass
class SpriteData:
    bank: int
    x: int
    y: int
    width: int
    height: int


def _load_sprite_data() -> None:
    global SPRITE_DATA
    data_path = ASSETS_PATH / "sprite_data.json"
    with open(data_path, "r") as f:
        data = json.load(f)

    for k, v in data.items():
        SPRITE_DATA[k] = SpriteData(**v)

def _load_image_banks() -> None:
    for i in range(3):
        bank = ASSETS_PATH / f"bank_{i}.png"
        pyxel.images[i].load(0, 0, str(bank))


_load_sprite_data()
_load_image_banks()

