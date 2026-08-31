from typing import Optional

import pygame

from .config import MainData
from .enums import Direction


class Fruit:
    def __init__(self, val: int = 0, parent: Optional["Cell"] = None):
        self.val = val
        self.parent = parent

    @property
    def image(self):
        names = ("no_dot.png", "small_dot.png", "big_dot.png")
        return MainData.assets.get_asset(names[self.val])

    def eated(self):
        pacmap = MainData.pacmap
        if self.val == 1:
            pacmap.score += MainData.config_from_file["points_per_pacgum"]
        elif self.val == 2:
            pacmap.score += MainData.config_from_file[
                "points_per_super_pacgum"
            ]
            pacmap.fright_time_left = MainData.pacmap.level[
                "frightened_duration"
            ]
        self.val = 0
        if self.parent is not None:
            self.parent.init_image()


class Cell:
    def __init__(
        self,
        walls: int,
        x: int,
        y: int,
        neighbors: list[list["Cell"]],
        fruit: Fruit,
    ):
        self.walls = walls
        self.fruit = fruit if walls != 15 else Fruit(0)
        if self.fruit:
            self.fruit.parent = self
        self.x = x
        self.y = y
        self.neighbors = neighbors

    @property
    def image(self):
        if getattr(self, "__image", None) is None:
            self.init_image()
        return self.__image

    def __get_neighbor(self):
        grid = [[0 for _ in range(3)] for _ in range(3)]

        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                x = self.x + dx
                y = self.y + dy

                if (0 <= x < len(self.neighbors)
                        and 0 <= y < len(self.neighbors[x])):
                    grid[dy + 1][dx + 1] = self.neighbors[x][y].walls

        return grid

    def init_image(self):
        def get_corner(
            walls: int,
            dir1: Direction,
            dir2: Direction,
            neighbor: tuple[int, int, int, int],
        ):
            if dir1.value & walls and dir2.value & walls:
                return MainData.assets.get_asset(
                    f"corner_{'n' if dir1 == Direction.NORTH else 's'}"
                    + f"{'e' if dir2 == Direction.EAST else 'w'}.png"
                )
            elif dir1.value & walls:
                return MainData.assets.get_asset(
                    (
                        f"double_{'top' if dir1 == Direction.NORTH
                                  else 'bottom'}"
                    )
                    + ".png"
                )
            elif dir2.value & walls:
                return MainData.assets.get_asset(
                    (
                        f"double_{'right' if dir2 == Direction.EAST
                                  else 'left'}")
                    + ".png"
                )
            else:
                return MainData.assets.get_asset(
                    "very_small_corner_"
                    + f"{'n' if dir1 != Direction.NORTH else 's'}"
                    + f"{'e' if dir2 != Direction.EAST else 'w'}.png"
                )

        def get_direction(walls: int, direction: Direction):
            if direction == Direction.NORTH and walls & direction.value:
                return MainData.assets.get_asset("double_top.png")
            elif direction == Direction.EAST and walls & direction.value:
                return MainData.assets.get_asset("double_right.png")
            elif direction == Direction.SOUTH and walls & direction.value:
                return MainData.assets.get_asset("double_bottom.png")
            elif direction == Direction.WEST and walls & direction.value:
                return MainData.assets.get_asset("double_left.png")
            else:
                return MainData.assets.get_asset("no_dot.png")

        if self.walls == 15:
            pass  # create 3*3 full block for 42 patern

        n = self.__get_neighbor()
        all_images = (
            (
                get_corner(self.walls, Direction.NORTH, Direction.WEST, n),
                get_direction(self.walls, Direction.WEST),
                get_corner(self.walls, Direction.SOUTH, Direction.WEST, n),
            ),  # right part
            (
                get_direction(self.walls, Direction.NORTH),
                self.fruit.image
                if self.fruit
                else MainData.assets.get_asset("no_dot.png"),
                get_direction(self.walls, Direction.SOUTH),
            ),  # midle
            (
                get_corner(self.walls, Direction.NORTH, Direction.EAST, n),
                get_direction(self.walls, Direction.EAST),
                get_corner(self.walls, Direction.SOUTH, Direction.EAST, n),
            ),  # left
        )
        self.__image = pygame.surface.Surface(
            (MainData.cell_size * 3, MainData.cell_size * 3)
        )
        for x in range(3):
            for y in range(3):
                all_images[x][y].set_colorkey((0, 0, 0))
                color = (20, 20, 80)
                if (self.x + self.y + x + y) % 2:
                    color = (0, 0, 0)
                self.__image.fill(
                    color,
                    (
                        x * MainData.cell_size,
                        y * MainData.cell_size,
                        MainData.cell_size,
                        MainData.cell_size,
                    ),
                )
        self.__image.blits(
            [
                (image, (x * MainData.cell_size, y * MainData.cell_size))
                for x, image_col in enumerate(all_images)
                for y, image in enumerate(image_col)
            ]
        )
        return self.__image

    def __str__(self):
        return hex(self.walls)[2:]

    __repr__ = __str__
