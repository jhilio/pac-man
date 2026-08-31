from src.enums import Direction
from src.vector import Pos2D

from ..config import MainData
from .moving_entity import MovingEntities


class Pacman(MovingEntities):
    def __init__(
        self, direction: Direction, x: int = 0, y: int = 0, lives: int = 3
    ):
        super().__init__(direction, x, y)
        self.lives = lives
        self.speed = MainData.pacmap.level["pacman_speed"] / 100
        self.fright_speed = MainData.pacmap.level["pacman_fright_speed"] / 100
        self.cheat_mode = False
        self.map = MainData.pacmap

    @property
    def raw_image(self):
        frame = MainData.assets.get_asset(
            f"pacman_frame_{self.anim_step}.png", size_multiplier=1.3
        )
        return frame

    @property
    def image(self):
        frame = MainData.assets.get_asset(
            f"pacman_frame_{self.anim_step}.png", size_multiplier=1.3
        )
        rotated = self.direction.rotate(frame)
        return rotated

    def incr_anim(self):
        self.anim_step = (
            self.anim_step + 1
        ) % 4  # 4 is pacman anim frame lenght

    def update_level_data(self):
        self.speed = MainData.pacmap.level["pacman_speed"] / 100
        self.fright_speed = MainData.pacmap.level["pacman_fright_speed"] / 100

    def step(self):
        self.move(self.turn_and_pathfind())
        cell_x, cell_y = self.cell_pos
        if self.map.cells[cell_x][cell_y].fruit is not None:
            self.map.cells[cell_x][cell_y].fruit.eated()

    def turn_and_pathfind(self):
        new_pos = self.next_pos
        cell_x, cell_y = (new_pos) // 3
        cell_walls = self.map.cells[cell_x][cell_y].walls

        if self.next_direction != self.direction and (new_pos % (3, 3)) == (
            1,
            1,
        ):
            if self.cheat_mode:
                self.direction = self.next_direction  # fast turn in cheat mode
            if cell_walls & self.next_direction.value:  # if wall blocked
                if (
                    self.next_direction != self.direction.oppo()
                ):  # fast turn back
                    self.next_direction = self.direction
            else:
                self.direction = self.next_direction  # empty buffer

        if (
            not cell_walls & self.direction.value  # wall open
            or (
                ((new_pos) % (3, 3))[0] != 1 and self.direction.delta()[0]
            )  # or continue x
            or (
                ((new_pos) % (3, 3))[1] != 1 and self.direction.delta()[1]
            )  # or continue y
        ):
            new_pos += self.direction.delta()

        if (
            self.next_direction != self.direction
            and not cell_walls & self.next_direction.value
            and new_pos % (3, 3) == (1, 1)
        ):
            self.direction = self.next_direction
            new_pos += self.direction.delta()
        return new_pos

    def eat_wall(self):
        if self.cheat_mode:
            facing_cell_x, facing_cell_y = (
                self.next_pos // 3
            ) + self.direction.delta()
            if not (
                0 <= facing_cell_x < len(self.map.cells)
                and 0 <= facing_cell_y < len(self.map.cells[0])
            ):
                return
            cell_x, cell_y = self.next_pos // 3
            self.map.cells[cell_x][cell_y].walls &= ~self.direction.value
            self.map.cells[facing_cell_x][
                facing_cell_y
            ].walls &= ~self.direction.oppo().value
            self.map.cells[cell_x][cell_y].init_image()
            for neig_x, neig_y in [
                (Pos2D(cell_x, cell_y)) + direc.delta() for direc in Direction
            ]:
                if 0 <= neig_x < len(self.map.cells) and 0 <= neig_y < len(
                    self.map.cells[0]
                ):
                    cell = self.map.cells[neig_x][neig_y]
                    cell.init_image()
