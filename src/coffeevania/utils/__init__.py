from typing import Protocol

from coffeevania.components.collision import CollisionRectangle
from coffeevania.components.position import Position


class Collidable(Protocol):
    position: Position
    collision: CollisionRectangle


def overlaps(a: Collidable, b: Collidable) -> bool:
    return (
        a.position.x < b.position.x + b.collision.width
        and a.position.x + a.collision.width > b.position.x
        and a.position.y < b.position.y + b.collision.height
        and a.position.y + a.collision.height > b.position.y
    )

def clamp(n: float, a: float, b: float) -> float:
    if a > b:
        raise ValueError(f"Tried to use clamp with a > b: a={a}, b={b}")
    if n < a:
        n = a
    if n > b:
        n = b

    return n

def lerp(a: float, b: float, easing_factor: float, epsilon: float = 0.0) -> float:
    ret = a + (b - a) * easing_factor
    if abs(b - ret) < epsilon:
        return b
    return ret
