from .ghost import Ghost
from ..vector import Pos2D
from ..config import MainData


class Blinky(Ghost):
    ghost_color = (255, 0, 0)
    ghost_name = "blinky"

    def specific_chase_cell(self) -> Pos2D:
        """blinky always try to reach pacman directly"""
        target: Pos2D = MainData.pacmap.pacman.pos
        return target
