from .ghost import Ghost
from ..vector import Pos2D
from ..config import MainData


class Clyde(Ghost):
    ghost_color = (255, 127, 80)
    ghost_name = "clyde"

    def specific_chase_cell(self) -> Pos2D:
        """
        clyde try to reach pacman directly until they are 8 or less cell apart
        if they are close clyde try to go to his corner
        """
        if (
            Pos2D(0, 0).pythagore(
                self.pos.abs_diff(MainData.pacmap.pacman.pos)
            )
            >= 8
        ):
            target: Pos2D = MainData.pacmap.pacman.pos

        else:
            target = self.original_pos
        return target
