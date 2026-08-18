from re import S
from typing import Optional
import pygame
from pathlib import Path
from .config import Config

NORTH = 1
EAST = 2
SOUTH = 4
WEST = 8

assets_names = [
    "very_small_corner_ne.png",
    "very_small_corner_se.png",
    "very_small_corner_sw.png",
    "very_small_corner_nw.png",
    "small_corner_ne.png",
    "small_corner_se.png",
    "small_corner_sw.png",
    "small_corner_nw.png",
    "corner_ne.png",
    "corner_se.png",
    "corner_sw.png",
    "corner_nw.png",
    "double_top.png",
    "double_right.png",
    "double_left.png",
    "double_bottom.png",
    "no_dot.png",
    "small_dot.png",
    "middle_dot.png",
    "big_dot.png",
]

sprites = {
    name: pygame.image.load(str(Path("assets") / "double" / name))
    for name in assets_names
}

for im in sprites.values():
    im.set_colorkey((0, 0, 0))


class Fruit:
    cls_images = (sprites["no_dot.png"], sprites["small_dot.png"], sprites["big_dot.png"])

    def __init__(self, val:int = 0):
        self.val = val

    @property
    def image(self):
        return pygame.transform.scale(self.cls_images[self.val], (Config.cell_size, Config.cell_size))


    def eated(self):
        score = self.val *100
        self.val = 0
        return score


class Cell:
    def __init__(
        self,
        walls: int,
        x: int,
        y: int,
        neighbors: list[list["Cell"]],
        fruit: Optional[Fruit] = None,
    ):
        self.walls = walls
        self.fruit = fruit if walls != 15 else Fruit(0)
        self.x = x
        self.y = y
        self.neighbors = neighbors
        self.__image = None

    @property
    def image(self):
        if self.__image is None:
            self.init_image()
        return self.__image

    def __get_neighbor(self):
        grid = [[0 for _ in range(3)] for _ in range(3)]

        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                x = self.x + dx
                y = self.y + dy

                if 0 <= x < len(self.neighbors) and 0 <= y < len(self.neighbors[x]):
                    grid[dy + 1][dx + 1] = self.neighbors[x][y].walls

        return grid

    def init_image(self):
        def get_corner(walls: int, dir1, dir2, neighbor: tuple[int, int, int, int]):
            if dir1 & walls and dir2 & walls:
                return sprites[f"corner_{'n' if dir1 == NORTH else 's'}{'e' if dir2 == EAST else 'w'}.png"]
            elif dir1 & walls:
                return sprites[f"double_{'top' if dir1 == NORTH else 'bottom'}.png"]
            elif dir2 & walls:
                return sprites[f"double_{'right' if dir2 == EAST else 'left'}.png"]
            else:
                return sprites[f"very_small_corner_{'n' if dir1 != NORTH else 's'}{'e' if dir2 != EAST else 'w'}.png"]
        def get_direction(walls: int, direction: int):
            if direction == NORTH and walls & direction:
                return sprites[f"double_top.png"]
            elif direction == EAST and walls & direction:
                return sprites[f"double_right.png"]
            elif direction == SOUTH and walls & direction:
                return sprites[f"double_bottom.png"]
            elif direction == WEST and walls & direction:
                return sprites[f"double_left.png"]
            else:
                return sprites[f"no_dot.png"]
        if self.walls == 15:
            pass # create 3*3 full block for 42 patern

        n = self.__get_neighbor()

        self.__image = (
            (
                get_corner(self.walls, NORTH, WEST, n),
                get_direction(self.walls, WEST),
                get_corner(self.walls, SOUTH, WEST, n),
            ),  # right part
            (
                get_direction(self.walls, NORTH),
                sprites["no_dot.png"],
                get_direction(self.walls, SOUTH),
            ),  # midle
            (
                get_corner(self.walls, NORTH, EAST, n),
                get_direction(self.walls, EAST),
                get_corner(self.walls, SOUTH, EAST, n),
            ),  # left
        )
        return self.__image

    def __str__(self):
        return hex(self.walls)[2:]

    __repr__ = __str__
