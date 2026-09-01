import numpy as np

from ..charachters.ghost import Ghost
from ..enums import Direction


class ObservationBuilder:

    @staticmethod
    def build(
        state: tuple[
            list[list[int]],
            list[list[int]],
            tuple[int, int],
            list[Ghost],
            int,
            float,
        ],
        ghost_count: int = 4,
    ) -> tuple[np.ndarray, int, float]:
        """format given wall, fruit, and charachters data in a numpy ndarray
        Args:
            state: tuple[
                list[list[int]] : list of fruit
                list[list[int]] : list of wall
                tuple[int, int] : pos of pacman
                list[Ghost] : list of ghost
                int: score of the map
                float: 0-1 of curetnt frightened duration left
                ]:
            ghost_count (int, optional):
                used  to calculate ndarray size.
                Defaults to 4.
        Returns:
            tuple[np.ndarray, int, float]: the formated data
        """
        (
            walls_data,
            fruits_data,
            pacman_pos,
            ghosts,
            score,
            fright_time_ratio,
        ) = state
        height = len(walls_data)
        width = len(walls_data[0])
        channels = 6 + ghost_count

        observation = np.zeros(
            (channels, height, width),
            dtype=np.float32,
        )
        for x in range(height):
            for y in range(width):
                walls = walls_data[x][y]
                observation[0, x, y] = bool(walls & Direction.NORTH.value)
                observation[1, x, y] = bool(walls & Direction.EAST.value)
                observation[2, x, y] = bool(walls & Direction.SOUTH.value)
                observation[3, x, y] = bool(walls & Direction.WEST.value)
                observation[4, x, y] = fruits_data[x][y]

        pacman_x = pacman_pos[0] // 3
        pacman_y = pacman_pos[1] // 3

        observation[5, pacman_x, pacman_y] = 1.0
        for i, ghost in enumerate(ghosts):
            ghost_pos = ghost.pos
            ghost_x = int(ghost_pos[0] // 3)
            ghost_y = int(ghost_pos[1] // 3)
            observation[6 + i, ghost_x, ghost_y] = ghost.direction.value
        return observation, score, fright_time_ratio
