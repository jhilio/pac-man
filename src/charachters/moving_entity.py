import pygame
from ..config import MainData
from ..enums import Direction
from abc import ABC, abstractmethod
from ..vector import Pos2D




class MovingEntities(ABC):
    def __init__(self, direction: Direction, x: int=0, y: int=0):
        self.pos = Pos2D(x * 3, y *3) + (1, 1)
        self.original_pos = self.pos
        self.next_pos = self.pos
        self.direction = direction 
        self.next_direction = direction
        self.offset = 0
        self.anim_step = 0
        self.speed = 1
        self.fright_speed = 1
        self.is_alive = True

    def reset_pos(self):
        self.pos = self.original_pos
        self.next_pos = self.original_pos

    def update(self, dt:float):
        if MainData.pacmap.fright_time_left:
            self.offset += dt * self.fright_speed
        else:
            self.offset += dt * self.speed
        while self.offset >= 1:
            self.offset -= 1
            self.step()

    @property
    @abstractmethod
    def image(self) ->pygame.Surface:
        pass

    @abstractmethod
    def update_level_data(self):
        pass

    @abstractmethod
    def incr_anim(self):
        pass

    def move(self, new_pos: Pos2D):
        self.pos, self.next_pos = self.next_pos, new_pos


    @property
    def visual_pos(self):
        if MainData.pacmap.pacman.cheat_mode:
            return self.pos - (0.25, 0.25)
        return (self.pos - (0.25,0.25)).lerp(self.next_pos - (0.25, 0.25), self.offset)

    @property
    def cell_pos(self):

        return (self.pos) // 3


    def __str__(self):
        return self.__class__.__name__