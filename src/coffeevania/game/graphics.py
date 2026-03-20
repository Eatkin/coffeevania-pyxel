
from dataclasses import dataclass


@dataclass
class Sprite:
    bank: int
    src_x: int
    src_y: int
    width: int = 8
    height: int = 8
    frame_count: int = 1
    frame_duration: int = 8
