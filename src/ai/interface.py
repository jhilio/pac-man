from math import log2

import numpy
import torch

from ..enums import Direction
from ..pacmap import PacMap
from .network import PacmanNetwork
from .observation import ObservationBuilder


class NNDirectionChooser:

    def __init__(self, network: PacmanNetwork):
        self.network = network

    def _get_distribution(
        self,
        pacmap: PacMap
    ) -> tuple[numpy.ndarray, torch.Tensor]:
        """give current pacmap info to self.network and filter possible result
        Args:
            pacmap (PacMap): the map is needed to get current state
        Returns:
            tuple[numpy.ndarray, torch.Tensor]:
                the pacmap observation
                and the result Tensor containing the logits
                    for each direction
        """
        info = pacmap.get_state_for_nn()
        observation, _score, fright_time_ratio = ObservationBuilder.build(info)
        tensor = torch.from_numpy(observation).unsqueeze(0)
        fright_tensor = torch.tensor(
            [[fright_time_ratio]],
            dtype=torch.float32,
        )
        pacman_cell = numpy.argwhere(observation[5] == 1)[0]
        pacman_x, pacman_y = pacman_cell
        logits = self.network(tensor, fright_tensor, (pacman_x, pacman_y))

        walls = observation[0:4, pacman_x, pacman_y]
        for i in range(4):
            if walls[i] == 1:
                logits[0, i] = float("-inf")

        if sum(walls[0:4]) != 3:
            opposite = int(log2(pacmap.pacman.direction.oppo().value))
            logits[0, opposite] = float("-inf")
        return observation, logits

    def choose(self, pacmap: PacMap, temperature: float = 1.0) -> Direction:
        """get the distribution of
        response and chose using softmax
        and the given temperature
        Args:
            pacmap (PacMap): map for which to decide
            temperature (float, optional):
                low = randow high = obtuse.
                Defaults to 1.0.
        Returns:
            Direction: chosen direction
        """
        with torch.no_grad():
            _observation, logits = self._get_distribution(pacmap)
            probabilities = torch.softmax(
                logits / temperature,
                dim=1,
            )
            action = torch.multinomial(
                probabilities,
                1,
            ).item()
        return Direction(1 << int(action))
