from encodings.punycode import T
import json
from random import choices

from .charachters.clyde import Clyde

from .charachters.ghost import Ghost
from .charachters.moving_entity import MovingEntities
from .charachters.inky import Inky
from .charachters.pacman import Pacman
from .charachters.blinky import Blinky
from .charachters.pinky import Pinky
from .enums import Direction
from .cells import Cell, Fruit
from .config import MainData
import mazegenerator



class PacMap:
    def __init__(self, maze: mazegenerator.MazeGenerator):
        MainData.pacmap = self
        self.level_num = 1
        self.level = MainData.config_from_file["levels"][str(self.level_num)]
        self.maze = maze
        self.offset = 0
        self.score = 0
        self.fright_time_left = 0
        self.total_elapsed_time = 0
        self.phase_timer = 0
        self.player_name = input("name_of player :")
        self.init_cells()
        self.init_charachters()

    def regenerate(self):
        self.maze._seed += 1
        self.fright_time_left = 0
        self.total_elapsed_time = 0
        self.phase_timer = 0
        self.maze.generate()
        self.init_cells()
        for ghost in self.ghosts:
            ghost.reset_pos()
        self.pacman.reset_pos()


    def init_charachters(self):
        self.pacman = Pacman(Direction.NORTH, x=len(self.maze.maze)//2, y=len(self.maze.maze[1])//2, lives=MainData.config_from_file["lives"])
        self.blinky = Blinky(Direction.SOUTH, len(self.cells)-1, 0)
        self.pinky = Pinky(Direction.EAST)
        self.inky = Inky(Direction.WEST, len(self.cells)-1, len(self.cells[0])-1)
        self.clyde = Clyde(Direction.NORTH, 0, len(self.cells[0])-1)
        self.ghosts: list[Ghost]= [self.blinky, self.pinky, self.inky, self.clyde]


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
                                weights=[200.2, 0.8])[0]
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
        self.total_elapsed_time += dt
        self.phase_timer += (dt - self.fright_time_left if dt - self.fright_time_left > 0 else 0)
        if self.fright_time_left >0:
            self.fright_time_left -= dt
            if self.fright_time_left < 0:
                self.fright_time_left = 0
        dt *= MainData.tick_rate
        self.offset += dt
        self.pacman.update(dt)
        for ghost in self.ghosts:
            ghost.update(dt)
        if self.offset > 1:
            dt-=1
            self.step()
        self.check_colision()

    def check_colision(self):
        for ghost in self.ghosts:
            if ghost.pos == self.pacman.pos and ghost.is_alive:
                self.colision_effect(ghost)

    def step(self):
        a = sum(cell.fruit.val for row in self.cells for cell in row)
        if not a:
            self.go_next_level()
        if self.total_elapsed_time > self.level["duration"]:
            self.pacman_died()
         
    def go_next_level(self):
        self.level_num +=1
        self.level = MainData.config_from_file["levels"][str(self.level_num)]
        for ghost in self.ghosts:
            ghost.update_level_data()
        self.pacman.update_level_data()
        self.regenerate()

    def colision_effect(self, ghost: Ghost):
        if self.fright_time_left and ghost.is_alive:
            ghost.is_alive = False
            self.score += MainData.config_from_file["points_per_ghost"]
        else:
            self.pacman_died()

    def pacman_died(self):
        for ghost in self.ghosts:
            ghost.reset_pos()
            ghost.is_alive = True
        if not self.pacman.cheat_mode:
            self.pacman.reset_pos()
            self.pacman.lives -= 1


    def save_high_score(self):
        if not self.player_name:
            return
        k = 10
        MainData.high_scores[self.player_name] = max(self.score, MainData.high_scores.get(self.player_name, 0))

        scores =  MainData.high_scores
        sorted_scores ={k: scores[k] for k in sorted(scores, key=lambda _, it=iter(scores): next(it))}
        top_k = {k:v  for i, (k, v) in zip(range(k),sorted_scores.items())}
        MainData.high_scores = top_k