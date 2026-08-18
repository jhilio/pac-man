import pygame

from ..enums import Direction, GhostState
from abc import ABC, abstractmethod
from ..vector import Pos2D




class MovingEntities(ABC):
    anim_step = 0
    anim_frames: list|dict = []


    def __init__(self, context: 'PacMap', direction: Direction, x: int=0, y: int=0):
        self.pos = Pos2D(x * 3, y *3) + (1, 1)
        self.original_pos = self.pos
        self.offset = 0
        self.direction = direction 
        self.next_direction = direction
        self.is_alive = True
        self.map = context
        self.next_pos = self.pos
        self.anim_step = 0

    def reset_pos(self):
        self.pos = self.original_pos
        self.next_pos = self.original_pos

    @abstractmethod
    def update(self, dt:float):
        pass

    @property
    @abstractmethod
    def image(self) ->pygame.Surface:
        pass

    @abstractmethod
    def incr_anim(self):
        pass

    def move(self, new_pos: Pos2D):
        self.pos, self.next_pos = self.next_pos, new_pos


    @property
    def visual_pos(self):
        return (self.pos - (0.25,0.25)).lerp(self.next_pos - (0.25, 0.25), self.offset)

    @property
    def cell_pos(self):
        return (self.pos) // 3


class Ghost(MovingEntities):
    def __init__(self, context, direction, x = 0, y = 0):
        super().__init__(context, direction, x, y)
        self.mode = GhostState.SCATER
        self.target_cell = self.choose_target_cell()

    @abstractmethod
    def choose_target_cell(self) -> Pos2D:
        pass

    def rank_neighbor(self):
        new_pos = self.next_pos
        cell_x, cell_y = new_pos // 3
        if (new_pos % (3, 3) != (1,1)):
            valide_dirs = [self.direction]
        else:
            valide_dirs = [
            direc for direc in Direction 
                if (
                    not self.map.cells[cell_x][cell_y].walls & direc.value
                    and self.direction != direc.oppo()
                )
            ]
        if not valide_dirs:
            valide_dirs = [self.direction.oppo()]
        ranked = sorted(
            valide_dirs,
            key=lambda direc: (
                (new_pos + direc.delta()).pythagore(self.target_cell),
                direc.pac_order()
            )
        )
        return ranked