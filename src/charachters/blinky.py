
from src.vector import Pos2D

from .abstract_chars import Ghost, GhostState, Direction
from ..config import Config
import pygame






class Blinky(Ghost):

    def __init__(self, context, direction, x=0, y=0):
        super().__init__(context, direction, x, y)

    @property
    def image(self):
        frame = Config.assets.get_asset(
            f"blinky_{self.direction.to_text()}{self.anim_step+1}.png",
            size_multiplier=1.5)
        return frame

    def incr_anim(self):
        self.anim_step == 0 if self.anim_step else 1

    def choose_target_cell(self):
        self.target_cell = self.map.pacman.pos
        if self.target_cell == self.pos:
            self.target_cell = Pos2D(0, 0)

    def update(self, dt):
        self.offset += dt *0.5
        if self.offset >= 1:
            self.offset -= 1
            self.step()

    def step(self):
        self.choose_target_cell()
        self.direction = self.rank_neighbor()[0]
        self.move(self.next_pos + self.direction.delta())



