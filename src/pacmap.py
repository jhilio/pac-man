from itertools import count
from random import choices

from .charachters import Pacman
from .enums import Direction

from .cells import Cell, Fruit
import mazegenerator



class PacMap:
    def __init__(self, maze: mazegenerator.MazeGenerator):
        self.maze = maze
        self.offset = 0
        self.score = 0
        self.init_cells()
        self.pacman = Pacman(self, Direction.NORTH, x=len(self.maze.maze)//2, y=len(self.maze.maze[1])//2)

    def regenerate(self):
        self.maze._seed += 1
        self.maze.generate()
        self.init_cells()

    def init_cells(self):
        self.cells: list[list[Cell]] = []

        for x in range(len(self.maze.maze)):
            column = []
            self.cells.append(column)
            for y in range(len(self.maze.maze[0])):
                column.append(
                    Cell(self.maze.maze[y][x], x, y, self.cells,
                        fruit=Fruit(
                            choices(
                                population=[0, 1],
                                weights=[0.2, 0.8])[0]
                        )
                    )
                )
        self.cells[0][0].fruit = Fruit(2)
        self.cells[0][-1].fruit = Fruit(2)
        self.cells[-1][0].fruit = Fruit(2)
        self.cells[-1][-1].fruit = Fruit(2)

    def __str__(self):
        return "\n".join(
            " ".join(str(self.cells[x][y]) for x in range(len(self.cells[0])))
            for y in range(len(self.cells))
        )

    def update(self, dt:float):
        self.offset += dt
        self.pacman.update(dt)
        if self.offset > 1:
            dt-=1
            self.step()
        

    def step(self):
        a = sum(cell.fruit.val for row in self.cells for cell in row)
        if not a:
            self.regenerate()
