import pygame
from ..config import MainData
from ..enums import Direction
from abc import ABC, abstractmethod
from ..vector import Pos2D


class MovingEntities(ABC):
    def __init__(self, direction: Direction, x: int = 0, y: int = 0):
        """create a MovingEntities
        Args:
            direction (Direction): start direction the Entity is Facing
            x (int, optional):
                starting x will be used as reset pos.
                Defaults to 0.
            y (int, optional):
                starting y will be used as reset pos.
                Defaults to 0.
        """
        self.pos = Pos2D(x * 3, y * 3) + (1, 1)
        self.original_pos = self.pos
        self.next_pos = self.pos
        self.direction = direction
        self.next_direction = direction
        self.offset = 0.0
        self.anim_step = 0
        self.speed = 1.0
        self.fright_speed = 1.0
        self.is_alive = True

    def reset_pos(self) -> None:
        """reset pos to the one given at creation"""
        self.pos = self.original_pos
        self.next_pos = self.original_pos

    def update(self, dt: float) -> None:
        """advance through time depending on speed
        Args:
            dt (float): time since last frame
        """
        if MainData.pacmap.fright_time_left:
            self.offset += dt * self.fright_speed
        else:
            self.offset += dt * self.speed
        while self.offset >= 1:
            self.offset -= 1
            self.step()

    @abstractmethod
    def step(self) -> None:
        pass

    @property
    @abstractmethod
    def image(self) -> pygame.Surface:
        pass

    @abstractmethod
    def update_level_data(self) -> None:
        pass

    @abstractmethod
    def incr_anim(self) -> None:
        pass

    def move(self, new_pos: Pos2D) -> None:
        self.pos, self.next_pos = self.next_pos, new_pos

    @property
    def visual_pos(self) -> Pos2D:
        return (self.pos - (0.25, 0.25)).lerp(
            self.next_pos - (0.25, 0.25), self.offset
        )

    @property
    def cell_pos(self) -> Pos2D:
        return (self.pos) // 3

    def __str__(self) -> str:
        return self.__class__.__name__
