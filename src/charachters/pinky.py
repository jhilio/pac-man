from ..enums import Direction
from ..vector import Pos2D
from .ghost import Ghost, MainData


class Pinky(Ghost):
    ghost_color = (255, 182, 193)
    ghost_name = "pinky"

    def specific_chase_cell(self):
        pacman = MainData.pacmap.pacman
        target = (Pos2D(pacman.direction.delta()) * 4) + pacman.pos
        if pacman.direction == Direction.NORTH:
            target += Pos2D(Direction.WEST.delta()) * 4
        return target
