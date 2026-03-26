import csv
import os
from typing import List

# Constructs a large text file from all level chunks

# Global level settings
chunk_width, chunk_height = 45, 12

layout: List[List[str]] = []

with open("assets/levels/layout.csv", "r") as c:
    reader = csv.reader(c)
    layout = list(reader)

super_level: List[List[List[str]]] = []

empty_level = ["." * chunk_width for _ in range(chunk_height)]

for row in layout:
    levels: List[List[str]] = []
    for lvl in row:
        if not lvl:
            levels.append(empty_level)
            continue
        file = os.path.join("assets", "levels", f"{lvl}.txt")
        with open(file, "r") as f:
            data = [row.strip() for row in f.readlines()]
            levels.append(data)

    super_level.append(levels)

super_level_ascii = ""

# Now let us loop over our levels to construct the super level
for level_chunk_row in super_level:
    for i in range(chunk_height):
        for level in level_chunk_row:
            super_level_ascii += level[i]
        super_level_ascii += "\n"

with open("assets/levels/super-level.txt", "w") as f:
    f.write(super_level_ascii)
