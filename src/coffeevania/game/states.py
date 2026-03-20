from enum import Enum
from enum import auto


class CatState(Enum):
    IDLE = auto()
    RUNNING = auto()
    JUMPING = auto()
    FALLING = auto()
