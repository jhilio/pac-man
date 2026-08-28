from random import shuffle
from typing import Optional

from .moving_entity import (
    MovingEntities,
    Direction,
    MainData,
    Pos2D,
    abstractmethod,
)
from ..enums import GhostState


def get_ghost_state():
    phases: list[tuple[str, Optional[int]]] = MainData.pacmap.level["phases"]
    time_left = MainData.pacmap.phase_timer
    for mode, duration in phases:
        if duration is None or time_left < duration:
            return GhostState(mode.upper())
        time_left -= duration


class Ghost(MovingEntities):
    def __init__(self, direction: Direction, x=0, y=0):
        super().__init__(direction, x, y)
        self.mode = GhostState.SCATTER
        self.choose_target_cell()
        self.speed = MainData.pacmap.level["ghost_speed"] / 100
        self.fright_speed = MainData.pacmap.level["ghost_fright_speed"] / 100

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        if "ghost_name" not in cls.__dict__:
            raise TypeError(f"{cls.__name__} must define 'ghost_name'")
        if "ghost_color" not in cls.__dict__:
            raise TypeError(f"{cls.__name__} must define 'ghost_color'")

    def rank_neighbor(self):
        new_pos = self.next_pos
        cell_x, cell_y = new_pos // 3
        if new_pos % (3, 3) != (1, 1):
            valide_dirs = [self.direction]
        else:
            valide_dirs = [
                direc
                for direc in Direction
                if (
                    not MainData.pacmap.cells[cell_x][cell_y].walls
                    & direc.value
                    and self.direction != direc.oppo()
                )
            ]
        if not valide_dirs:
            valide_dirs = [self.direction.oppo()]
        ranked = sorted(
            valide_dirs,
            key=lambda direc: (
                (new_pos + direc.delta()).pythagore(self.target_cell),
                direc.pac_order(),
            ),
        )
        if self.mode == GhostState.FRIGHTENED:
            shuffle(ranked)
        return ranked

    @property
    def image(self):
        tl = f"{self.ghost_name}_{self.direction.to_text()}{self.anim_step+1}"
        path_name = ""
        fright_time = MainData.pacmap.fright_time_left
        if not self.is_alive:
            path_name = f"eyes_{self.direction.to_text()}.png"
        elif fright_time:
            if fright_time > 2 or fright_time % 0.5 > 0.3:
                path_name = f"frightened_{self.anim_step+1}.png"
            else:
                path_name = f"frightened_flash_{self.anim_step+1}.png"
        else:
            path_name = tl + ".png"

        frame = MainData.assets.get_asset(path_name, size_multiplier=1.3)
        return frame

    def update(self, dt: float):
        if self.pos == self.original_pos:
            self.is_alive = True
        if not self.is_alive:
            self.mode = GhostState.DEAD
        elif MainData.pacmap.fright_time_left:
            if self.mode != GhostState.FRIGHTENED:
                self.mode = GhostState.FRIGHTENED
                self.direction = self.direction.oppo()
        else:
            new_mode = get_ghost_state()
            if new_mode != self.mode and new_mode == GhostState.SCATTER:
                self.direction = self.direction.oppo()
            self.mode = new_mode
        super().update(dt)

    def incr_anim(self):
        self.anim_step = 0 if self.anim_step else 1

    def update_level_data(self):
        self.speed = MainData.pacmap.level["ghost_speed"] / 100
        self.fright_speed = MainData.pacmap.level["ghost_fright_speed"] / 100

    def choose_target_cell(self):
        if self.mode in [GhostState.DEAD, GhostState.SCATTER]:
            self.target_cell = self.original_pos
        else:
            self.target_cell = self.specific_chase_cell()

    def step(self):
        self.choose_target_cell()
        self.direction = self.rank_neighbor()[0]
        self.move(self.next_pos + self.direction.delta())

    @abstractmethod
    def specific_chase_cell(self) -> Pos2D:
        pass
