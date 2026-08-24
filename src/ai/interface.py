from ..enums import Direction
from .observation import ObservationBuilder
import torch
import numpy


class NNDirectionChooser:

    def __init__(self, network):
        self.network = network

    def _get_distribution(self, pacmap):
        info = pacmap.get_state_for_nn()
        observation, score, fright_time_ratio = (
            ObservationBuilder.build(info)
        )
        tensor = torch.from_numpy(observation).unsqueeze(0)
        fright_tensor = torch.tensor(
            [[fright_time_ratio]],
            dtype=torch.float32,
        )
        logits = self.network(
            tensor,
            fright_tensor,
        )
        pacman_cell = numpy.argwhere(observation[5] == 1)[0]
        pacman_x, pacman_y = pacman_cell
        walls = observation[0:4, pacman_x, pacman_y]
        for i in range(4):
            if walls[i] == 1:
                logits[0, i] = float("-inf")

        return observation, logits

    def choose(self, pacmap, temperature=2) -> Direction:
        with torch.no_grad():
            observation, logits = self._get_distribution(pacmap)
            probabilities = torch.softmax(
                logits / temperature,
                dim=1,
            )
            action = torch.multinomial(
                probabilities,
                1,
            ).item()
        return Direction(1 << action)

