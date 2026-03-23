from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from coffeevania.components.position import Position


if TYPE_CHECKING:
    from coffeevania.components.collision import CollisionRectangle


@dataclass
class Rect:
    x1: float
    x2: float
    y1: float
    y2: float


class Collidable(Protocol):
    position: Position
    collision: CollisionRectangle

    def destroy(self) -> None:
        pass


def overlaps(a: Collidable, b: Collidable) -> bool:
    """Checks if two instances are colliding"""
    return (
        a.position.x < b.position.x + b.collision.width
        and a.position.x + a.collision.width > b.position.x
        and a.position.y < b.position.y + b.collision.height
        and a.position.y + a.collision.height > b.position.y
    )


def rects_overlap(a: Rect, b: Rect) -> bool:
    """Checks if two arbitrary rects overlap"""
    return a.x1 < b.x2 and a.x2 > b.x1 and a.y1 < b.y2 and a.y2 > b.y1


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
