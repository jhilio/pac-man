from random import choices
from .charachters.pacman import Pacman
from .charachters.blinky import Blinky
from .enums import Direction
from .cells import Cell, Fruit
from .vector import Pos2D
from .config import Config
import mazegenerator



class PacMap:
    def __init__(self, maze: mazegenerator.MazeGenerator):
        self.config = Config.config_from_file
        self.maze = maze
        self.offset = 0
        self.score = 0
        self.init_cells()
        self.init_charachters()

    def regenerate(self):
        self.maze._seed += 1
        self.maze.generate()
        self.init_cells()
        for ghost in self.ghosts:
            ghost.reset_pos()
        self.pacman.reset_pos()

    def init_charachters(self):
        self.pacman = Pacman(self, Direction.NORTH, x=len(self.maze.maze)//2, y=len(self.maze.maze[1])//2, lives=self.config["lives"])
        self.blinky = Blinky(self, Direction.EAST)
        self.ghosts = [self.blinky]


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
        self.blinky.update(dt)
        if self.offset > 1:
            dt-=1
            self.step()
        self.check_colision()

    def check_colision(self):
        for elem in self.ghosts:
            if elem.pos == self.pacman.pos:
                for ghost in self.ghosts:
                    ghost.reset_pos()
                if not self.pacman.cheat_mode:
                    self.pacman.reset_pos()
                    self.pacman.lives -= 1
                break

    def step(self):
        a = sum(cell.fruit.val for row in self.cells for cell in row)
        if not a:
            self.regenerate()
        