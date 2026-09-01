from ..enums import Direction
from ..vector import Pos2D
from .ghost import Ghost, MainData


class Pinky(Ghost):
    ghost_color = (255, 182, 193)
    ghost_name = "pinky"

    def specific_chase_cell(self) -> Pos2D:
        """pinky try to go 4 cell in front of pacman"""
        pacman = MainData.pacmap.pacman
        target = (Pos2D(pacman.direction.delta()) * 4) + pacman.pos
        if pacman.direction == Direction.NORTH:
            target += Pos2D(Direction.WEST.delta()) * 4
        return target
