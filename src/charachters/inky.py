from ..enums import Direction
from ..vector import Pos2D
from .ghost import Ghost, MainData


class Inky(Ghost):
    ghost_color = (100, 200, 200)
    ghost_name = "inky"

    def specific_chase_cell(self):
        pacmap = MainData.pacmap
        pacman = pacmap.pacman
        ahead_pacman = (Pos2D(pacman.direction.delta()) * 2) + pacman.pos
        if pacman.direction == Direction.NORTH:
            ahead_pacman += Pos2D(Direction.WEST.delta()) * 2
        blinky_pos = pacmap.blinky.pos
        target = (ahead_pacman - blinky_pos) + ahead_pacman
        return target
