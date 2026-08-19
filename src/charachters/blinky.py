
from .ghost import Ghost, MainData

class Blinky(Ghost):
    ghost_color = (255, 127, 80)
    ghost_name = "blinky"
    def specific_chase_cell(self):
        return MainData.pacmap.pacman.pos


