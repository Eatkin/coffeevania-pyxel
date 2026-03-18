from coffeevania.common.game import GAME_HEIGHT
from coffeevania.common.game import GAME_WIDTH
from coffeevania.components.position import Position
from coffeevania.game import App
from coffeevania.game_objects.basic import Block
from coffeevania.game_objects.basic import Player
from coffeevania.game_objects.hazards import BouncingHazard


def main() -> None:
    game = App()
    game.create_entity(Player, position=Position(x=16, y=16))
    # Create a floor
    for i in range(0, GAME_WIDTH, 8):
        game.create_entity(Block, position=Position(x=i, y=GAME_HEIGHT - 8))

    # Create a random block to collide with
    game.create_entity(Block, position=Position(x=32, y=GAME_HEIGHT - 16))

    # Some bouncing hazard
    game.create_entity(BouncingHazard, position=Position(x=40, y=80))
    game.run()


if __name__ == "__main__":
    main()
