from .ghost import Ghost, MainData

class Clyde(Ghost):
    ghost_color = (255, 127, 80)
    ghost_name = "clyde"
    def specific_chase_cell(self):
        if sum(self.pos.abs_diff(MainData.pacmap.pacman.pos)) >= 8:
            return MainData.pacmap.pacman.pos
        else:
            return self.original_pos


