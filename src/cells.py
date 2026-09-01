from typing import Optional

import pygame
from pygame.surface import Surface

from .config import MainData
from .enums import Direction


class Fruit:
    def __init__(self, val: int = 0, parent: Optional["Cell"] = None):
        """init fruit with optional val and parend cell

        Args:
            val (int, optional): val of fruit.
                Defaults to 0.
            parent (Optional[Cell], optional):
                cell that cotain this fruit.
                Defaults to None.
        """
        self.val = val
        self.parent = parent

    @property
    def image(self) -> Surface:
        """return its coresponding image
        Returns:
            Surface: the image of the fruit
        """
        names = ("no_dot.png", "small_dot.png", "big_dot.png")
        return MainData.assets.get_asset(names[self.val])

    def eated(self) -> None:
        """update score and fright_time_left when eated
        then set self.val to 0 to avoid being eaten multiple time
        """
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
        fruit: Fruit,
    ):
        """init one Cell of the maze

        Args:
            walls (int): int from 0 to 15 represanting each wall
            x (int): x position of the cell
            y (int): y position of the cell
            fruit (Fruit): fruit to add to the cell
        """
        self.walls = walls
        self.fruit = fruit if walls != 15 else Fruit(0)
        if self.fruit:
            self.fruit.parent = self
        self.x = x
        self.y = y

    @property
    def image(self) -> Surface:
        """create the cell image if necesary, then return the image

        Returns:
            Surface: image represanting the cell + its fruit
        """
        if getattr(self, "__image", None) is None:
            self.init_image()
        return self.__image

    def init_image(self) -> Surface:
        """create 9 sub image and fuse them to represent each wall + fruit

        Returns:
            Surface: the fused 9 image
        """
        def get_corner(
            walls: int,
            dir1: Direction,
            dir2: Direction,
        ) -> Surface:
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

        def get_direction(walls: int, direction: Direction) -> Surface:
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

        all_images = (
            (
                get_corner(self.walls, Direction.NORTH, Direction.WEST),
                get_direction(self.walls, Direction.WEST),
                get_corner(self.walls, Direction.SOUTH, Direction.WEST),
            ),  # right part
            (
                get_direction(self.walls, Direction.NORTH),
                self.fruit.image
                if self.fruit
                else MainData.assets.get_asset("no_dot.png"),
                get_direction(self.walls, Direction.SOUTH),
            ),  # midle
            (
                get_corner(self.walls, Direction.NORTH, Direction.EAST),
                get_direction(self.walls, Direction.EAST),
                get_corner(self.walls, Direction.SOUTH, Direction.EAST),
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

    def __str__(self) -> str:
        return hex(self.walls)[2:]

    __repr__ = __str__
