import json
import os
import re
from dataclasses import asdict
from glob import glob
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

from PIL import Image

from coffeevania.game.graphics import SpriteData
from coffeevania.common import ASSETS_PATH

IMAGE_BANK_SIZE = (256, 256)  # width / height
GRID_SIZE = 8
IMAGE_BANK_CELLS: List[List[List[int]]]
IMAGE_BANK_CELLS = [
    [
        [0 for _ in range(IMAGE_BANK_SIZE[0] // GRID_SIZE)]
        for _ in range(IMAGE_BANK_SIZE[1] // GRID_SIZE)
    ]
    for _ in range(3)
]

# Setup the banks with empty cells
_bank = [
    [0 for _ in range(0, IMAGE_BANK_SIZE[0], GRID_SIZE)]
    * int(IMAGE_BANK_SIZE[1] / GRID_SIZE)
]
for i in range(3):
    IMAGE_BANK_CELLS.append(_bank[:])

IMAGE_BANK_ATLAS: List[Image.Image] = [
    Image.new(mode="RGBA", size=(256, 256)) for _ in range(3)
]


IMAGE_DATA: Dict[str, Dict[str, Any]] = {}


def find_image_bank_space(h_cells: int, v_cells: int) -> Dict[str, int]:
    for bank_idx, bank in enumerate(IMAGE_BANK_CELLS):
        rows = len(bank)
        cols = len(bank[0])
        for y in range(rows - v_cells + 1):
            for x in range(cols - h_cells + 1):
                if all(
                    bank[y + j][x + i] == 0
                    for i in range(h_cells)
                    for j in range(v_cells)
                ):
                    return {"bank": bank_idx, "cell_x": x, "cell_y": y}
    raise RuntimeError("No space left in image banks!")


def reserve_cells(cells: Dict[str, int], h_cells: int, v_cells: int) -> None:
    xstart = cells["cell_x"]
    ystart = cells["cell_y"]
    for i in range(h_cells):
        for j in range(v_cells):
            IMAGE_BANK_CELLS[cells["bank"]][ystart + j][xstart + i] = 1


def set_atlas(cells: Dict[str, int], im: Image.Image) -> None:
    sheet = IMAGE_BANK_ATLAS[cells["bank"]]
    x = cells["cell_x"] * GRID_SIZE
    y = cells["cell_y"] * GRID_SIZE
    sheet.paste(im, (x, y))


def update_image_data(
    cells: Dict[str, int], sprite_filename: str, sprite_size: Tuple[int, int]
) -> None:
    key = (
        os.path.basename(sprite_filename)
        .split(".png")[0]
        .replace("_", " ")
        .title()
        .replace(" ", "")
    )
    data = SpriteData(
        bank=cells["bank"],
        x=cells["cell_x"] * GRID_SIZE,
        y=cells["cell_y"] * GRID_SIZE,
        width=sprite_size[0],
        height=sprite_size[1],
    )

    IMAGE_DATA[key] = asdict(data)


def output_image_banks(output_dir: str) -> None:
    os.makedirs(output_dir, exist_ok=True)
    for i, bank in enumerate(IMAGE_BANK_ATLAS):
        bank.save(os.path.join(output_dir, f"bank_{i}.png"))


def main() -> None:
    sprites = glob(f"{ASSETS_PATH}/**/*.png", recursive=True)
    for sprite in sprites:
        # Ignore banks
        if re.match(r".*?bank_\d\.png$", sprite):
            print("Skipping", sprite)
            continue
        print("Placing sprite", sprite)
        im = Image.open(sprite)
        dim = im.size
        h_cells = dim[0] // GRID_SIZE
        v_cells = dim[1] // GRID_SIZE
        cells = find_image_bank_space(h_cells, v_cells)
        reserve_cells(cells, h_cells, v_cells)
        set_atlas(cells, im)
        update_image_data(cells, sprite, dim)

    output_image_banks("assets")

    with open("assets/sprite_data.json", "w") as f:
        json.dump(IMAGE_DATA, f, indent=2)


if __name__ == "__main__":
    main()
