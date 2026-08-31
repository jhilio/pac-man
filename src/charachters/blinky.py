
from .ghost import Ghost, MainData, Pos2D


class Blinky(Ghost):
    ghost_color = (255, 0, 0)
    ghost_name = "blinky"

    def specific_chase_cell(self) -> Pos2D:
        target: Pos2D = MainData.pacmap.pacman.pos
        return target
