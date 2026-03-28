import os
from typing import List

# Inverse process of level_concat
chunk_width, chunk_height = 45, 12
layout: List[List[str]] = []

with open("assets/levels/super-level.txt", "r") as f:
    level_text = [line for line in f.read().split("\n") if line.strip()]

world_width = len(level_text[0])
world_height = len(level_text)
chunks_wide = world_width // chunk_width
chunks_tall = world_height // chunk_height

rw = world_width % chunk_width
rh = world_height % chunk_height

if rw != 0 or rh != 0:
    print("WARNING: Chunk width / height is not correct - remainders - rw:", rw, ", rh:", rh)
    print("Actual width:", world_width, ", actual height:", world_height)

level_chunks: List[str] = []

for i in range(chunks_tall):
    y = i * chunk_height
    for j in range(chunks_wide):
        x = j * chunk_width
        # Take slices of the level
        slices: List[str] = []
        for k in range(chunk_height):
            s = level_text[y+k][x : x + chunk_width]
            slices.append(s)

        level_chunk = "\n".join(slices)
        level_chunks.append(level_chunk)

for i, chunk in enumerate(level_chunks, 1):
    os.makedirs("assets/levels/chunks", exist_ok=True)
    with open(f"assets/levels/chunks/chunk_{i:02}.txt", "w") as f:
        f.write(chunk)
