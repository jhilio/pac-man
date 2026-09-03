from random import shuffle
from abc import abstractmethod

from pygame.surface import Surface
from typing import Any
from .moving_entity import MovingEntities
from ..enums import GhostState, Direction
from ..config import MainData
from ..vector import Pos2D


def get_ghost_state() -> GhostState:
    """advance through the level phases and
    return curent one base on MainData.pacmap.phase_timer
    Raises:
        TypeError: if the name of a phase is nt str
        TypeError: if the duration of a phase is not int or None
    Returns:
        GhostState: current GhostState
    """
    phases: list[list[str | None | int]] = MainData.pacmap.level["phases"]
    time_left = MainData.pacmap.phase_timer
    for phase in phases:
        if isinstance(phase[0], str):
            mode: str = phase[0]
        else:
            raise TypeError("phase should start with a str")
        du_test = phase[1]
        if isinstance(du_test, (int, type(None))):
            duration: int | None = du_test
        else:
            raise TypeError("phase duratiton should be int or None")

        if duration is None or time_left < duration:
            return GhostState(mode.upper())
        time_left -= duration
    return GhostState.CHASE


class Ghost(MovingEntities):
    def __init__(self, direction: Direction, x: int = 0, y: int = 0):
        """create a ghoot

        Args:
            direction (Direction): start direction the ghost is facing
            x (int, optional):
                starting x will be used as prefered corner.
                Defaults to 0.
            y (int, optional):
                starting y will be used as prefered corner.
                Defaults to 0.
        """
        super().__init__(direction, x, y)
        self.mode = GhostState.SCATTER
        self.choose_target_cell()
        self.speed = MainData.pacmap.level["ghost_speed"] / 100
        self.fright_speed = MainData.pacmap.level["ghost_fright_speed"] / 100

    def __init_subclass__(cls, **kwargs: dict[str, Any]) -> None:
        """verify the subclass has initialised ghost_name and ghost_color

        Raises:
            TypeError: if ghost_name is not set
            TypeError: if ghost_color is not set
        """
        super().__init_subclass__(**kwargs)
        if "ghost_name" not in cls.__dict__:
            raise TypeError(f"{cls.__name__} must define 'ghost_name'")
        if "ghost_color" not in cls.__dict__:
            raise TypeError(f"{cls.__name__} must define 'ghost_color'")

    def rank_neighbor(self) -> list[Direction]:
        """filter possible direction and return the
        list of possible direction sorted by priority
        the sorting is done per distance to target cell
        and in case of tie Direction.pac_order
        Returns:
            list[Direction]: sorted list of direction
        """
        new_pos = self.next_pos
        cell_x, cell_y = int(new_pos.x // 3), int(new_pos.y // 3)
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
    def image(self) -> Surface:
        """
        create the corresponding image dependin
        on ghost_name and scale it to correct size
        Returns:
            Surface: the current image of the ghost
        """
        tl = (f"{getattr(self, "ghost_name", "no_name")}_"
              f"{self.direction.to_text()}{self.anim_step+1}")
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

    def update(self, dt: float) -> None:
        """advance the ghost through time
        Args:
            dt (float): how much time passed since last frame
        """
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

    def incr_anim(self) -> None:
        """togle anim image from 1 to 0
        """
        self.anim_step = 0 if self.anim_step else 1

    def update_level_data(self) -> None:
        """update the speed of the ghost depending on current level data
        """
        self.speed = MainData.pacmap.level["ghost_speed"] / 100
        self.fright_speed = MainData.pacmap.level["ghost_fright_speed"] / 100

    def choose_target_cell(self) -> None:
        """chose the targer cell depending on self.mode
        if self.mode in [GhostState.DEAD, GhostState.SCATTER]]:
            go to corner
        else
            depend on the self.specific_chase_cell of the ghost
        """
        if self.mode in [GhostState.DEAD, GhostState.SCATTER]:
            self.target_cell = self.original_pos
        else:
            self.target_cell = self.specific_chase_cell()

    def step(self) -> None:
        """finish the curent movement anim and chose the next cell
        """
        self.choose_target_cell()
        self.direction = self.rank_neighbor()[0]
        self.move(self.next_pos + self.direction.delta())

    @abstractmethod
    def specific_chase_cell(self) -> Pos2D:
        pass
