from random import Random

import mazegenerator

from .cells import Cell, Fruit
from .charachters.blinky import Blinky
from .charachters.clyde import Clyde
from .charachters.ghost import Ghost
from .charachters.inky import Inky
from .charachters.pacman import Pacman
from .charachters.pinky import Pinky
from .config import MainData
from .enums import Direction


class PacMap:
    def __init__(self, maze: mazegenerator.MazeGenerator):
        """initialise a pacmap from a maze generator
        Args:
            maze (mazegenerator.MazeGenerator):
                maze generator that will be used
        """
        MainData.set_pacmap(self)
        self.is_finished = False
        self.level_num = 1
        self.level = MainData.config_from_file["levels"][str(self.level_num)]
        self.maze = maze
        self.offset = 0.0
        self.score = 0
        self.has_started = False
        self.fright_time_left = 0.0
        self.total_elapsed_time = 0.0
        self.phase_timer = 0.0
        self.player_name = ""
        self.random = Random(self.maze._seed)
        self.training_mode = False
        # self.player_name = input("name_of player :")
        self.init_cells()
        self.init_charachters()

    def regenerate(self, maze_restart: bool = True) -> None:
        """regenerate the maze and reinitialise pos of pacman and each ghost

        Args:
            maze_restart (bool, optional):
                weither to regenerate the maze.
                Defaults to True.
        """
        self.has_started = False
        self.is_finished = False
        self.fright_time_left = 0
        self.total_elapsed_time = 0
        self.phase_timer = 0
        self.maze._seed += 1
        if maze_restart:
            self.maze.generate(seed=self.maze._seed)
        self.init_cells()
        for ghost in self.ghosts:
            ghost.reset_pos()
        self.pacman.reset_pos()
        self.pacman.direction = Direction.NORTH

    def restart(self, guard_map: bool = False) -> None:
        """complete restart of the game, going back to level 1
        and original lifes for pacman
        Args:
            guard_map (bool, optional):
                weither reuse the same seed or not.
                Defaults to False.
        """
        self.pacman.lives = MainData.config_from_file["lives"]
        self.level_num = 1
        if guard_map:
            self.maze._seed -= 1
        self.score = 0
        self.offset = 0.0
        self.regenerate(maze_restart=True)

    def init_charachters(self) -> None:
        """create each ghost and pacman
        """
        self.pacman = Pacman(
            Direction.NORTH,
            x=(len(self.cells) - 1) // 2,
            y=len(self.cells[0]) // 2,
            lives=MainData.config_from_file["lives"],
        )
        self.blinky = Blinky(Direction.SOUTH, len(self.cells) - 1, 0)
        self.pinky = Pinky(Direction.EAST)
        self.inky = Inky(Direction.WEST, len(
            self.cells) - 1, len(self.cells[0]) - 1)
        self.clyde = Clyde(Direction.NORTH, 0, len(self.cells[0]) - 1)
        self.ghosts: list[Ghost] = [
            self.blinky,
            self.pinky,
            self.inky,
            self.clyde,
        ]

    def init_cells(self) -> None:
        """initialise all cell based on self.maze.maze values
        """
        self.cells: list[list[Cell]] = []
        proporion = MainData.config_from_file["pacgum_proportion"]
        for x in range(len(self.maze.maze[0])):
            column: list[Cell] = []
            self.cells.append(column)
            for y in range(len(self.maze.maze)):
                column.append(
                    Cell(
                        self.maze.maze[y][x],
                        x,
                        y,
                        fruit=Fruit(
                            self.random.choices(
                                population=[0, 1],
                                weights=[
                                    1 - proporion,
                                    proporion
                                ],
                            )[0]
                        ),
                    )
                )
        self.cells[0][0].fruit = Fruit(2, self.cells[0][0])
        self.cells[0][-1].fruit = Fruit(2, self.cells[0][-1])
        self.cells[-1][0].fruit = Fruit(2, self.cells[-1][0])
        self.cells[-1][-1].fruit = Fruit(2, self.cells[-1][-1])

    def __str__(self) -> str:
        """format the maze to the hex representation of the cells

        Returns:
            str: the maze as hex
        """
        return "\n".join(
            " ".join(str(self.cells[x][y]) for x in range(len(self.cells[0])))
            for y in range(len(self.cells))
        )

    def update(self, dt: float) -> None:
        """update map timing and propagate
        update to each moving entities (pacman and ghost)
        Args:
            dt (float): time since last frame
        """
        self.has_started = True
        self.total_elapsed_time += dt
        self.phase_timer += max(0, dt - self.fright_time_left)
        if self.fright_time_left > 0:
            self.fright_time_left = max(self.fright_time_left - dt, 0)
        dt *= MainData.tick_rate
        self.offset += dt
        self.pacman.update(dt)
        for ghost in self.ghosts:
            ghost.update(dt)
        if self.offset > 1:
            dt -= 1
            self.step()
        self.check_colision()

    def check_colision(self) -> None:
        """check for colision between pacman pos and each ghost
        """
        for ghost in self.ghosts:
            if ghost.pos == self.pacman.pos and ghost.is_alive:
                self.colision_effect(ghost)

    def step(self) -> None:
        """test for level end and level timeout periodicaly
        """
        if sum(cell.fruit.val for row in self.cells for cell in row) == 0:
            self.go_next_level()
        if self.total_elapsed_time > self.level["duration"]:
            self.pacman_died()
            self.total_elapsed_time = 0

    def go_next_level(self) -> None:
        """step to next level and regenerate the map
        set self.is_finished to true if no next level exist
        """
        self.level_num += 1
        if MainData.config_from_file["levels"].get(str(self.level_num)):
            self.level = MainData.config_from_file["levels"][str(
                self.level_num)]
            for ghost in self.ghosts:
                ghost.update_level_data()
            self.pacman.update_level_data()
            self.regenerate()
        else:
            self.regenerate()
            self.is_finished = True

    def colision_effect(self, ghost: Ghost) -> None:
        """either pacman eat the ghost or the ghost kill pacman
        Args:
            ghost (Ghost): the ghost causing collision
        """
        if self.fright_time_left and ghost.is_alive:
            ghost.is_alive = False
            self.score += MainData.config_from_file["points_per_ghost"]
        else:
            self.pacman_died()

    def pacman_died(self) -> None:
        """reset ghost and if pacman is not in cheat mode,
        reset pacman and make him lose a life
        """
        for ghost in self.ghosts:
            ghost.reset_pos()
            ghost.is_alive = True
        if not self.pacman.cheat_mode:
            self.pacman.reset_pos()
            self.pacman.lives -= 1
            self.total_elapsed_time = 0
            if self.pacman.lives <= 0:
                self.is_finished = True

    def update_high_score(self) -> None:
        """update MainData.high_score by potentialy adding
        self.name: self.score if it reach the top 10
        if self.name == "" return early
        """
        if not self.player_name:
            return
        k = 10
        MainData.high_scores[self.player_name] = max(
            self.score, MainData.high_scores.get(self.player_name, 0)
        )

        scores = MainData.high_scores
        iterator = iter(scores.values())
        sorted_scores = {
            k: scores[k]
            for k in sorted(
                scores,
                key=lambda _: next(iterator),
                reverse=True,
            )
        }
        top_k = {k: v for i, (k, v) in zip(range(k), sorted_scores.items())}
        MainData.high_scores = top_k

    def get_state_for_nn(self) -> tuple[
        list[list[int]],
        list[list[int]],
        tuple[int, int],
        list[Ghost],
        int,
        float,
    ]:
        """format the state of the map to be used by a nn

        Returns:
            tuple[
                list[list[int]] : list of fruit
                list[list[int]] : list of wall
                tuple[int, int] : pos of pacman
                list[Ghost] : list of ghost
                int: score of the map
                float: 0-1 of curetnt frightened duration left
                ]:
        """
        fruits_data: list[list[int]] = []
        walls_data: list[list[int]] = []
        for x in range(len(self.cells)):
            current_wall_col: list[int] = []
            current_fruit_col: list[int] = []

            walls_data.append(current_wall_col)
            fruits_data.append(current_fruit_col)
            for y in range(len(self.cells[0])):
                current_wall_col.append(self.cells[x][y].walls)
                current_fruit_col.append(self.cells[x][y].fruit.val)

        pacman_pos: tuple[int, int] = (
            round(self.pacman.pos.x),
            round(self.pacman.pos.y)
        )
        fright_time: float = max(
            0.0,
            min(1.0, self.fright_time_left /
                self.level["frightened_duration"]),
        )
        return (
            walls_data,
            fruits_data,
            pacman_pos,
            self.ghosts,
            self.score,
            fright_time,
        )
