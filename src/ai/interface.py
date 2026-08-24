from ..enums import Direction
from .observation import ObservationBuilder
import torch
import numpy


class NNDirectionChooser:

    def __init__(self, network):
        self.network = network

    def _get_distribution(self, pacmap):
        info = pacmap.get_state_for_nn()
        observation, score = ObservationBuilder.build(info)

        tensor = torch.from_numpy(observation).unsqueeze(0)
        logits, value = self.network(tensor)

        pacman_cell = numpy.argwhere(observation[5] == 1)[0]
        pacman_x, pacman_y = pacman_cell
        walls = observation[0:4, pacman_x, pacman_y]

        for i in range(4):
            if walls[i] == pacmap.pacman.direction.oppo():
                logits[0, i] /= 2
            if walls[i] == 1:
                logits[0, i] = float("-inf")

        return observation, logits, value

    def _mask_walls(self, logits, observations):
        for batch in range(observations.shape[0]):
            pacman_cell = torch.nonzero(observations[batch, 5] == 1)[0]
            x, y = pacman_cell
            walls = observations[batch, 0:4, x, y]
            for i in range(4):
                if walls[i] == 1:
                    logits[batch, i] = float("-inf")


        return logits
    def choose(self, pacmap) -> Direction:
        with torch.no_grad():
            observation, logits,value = self._get_distribution(pacmap)
            probabilities = torch.softmax(logits, dim=1)
            chosen = torch.multinomial(probabilities, 1).item()
        return Direction(1 << chosen)

    def choose_training(self, pacmap):
        observation, logits,value = self._get_distribution(pacmap)
        distribution = torch.distributions.Categorical(logits=logits)
        action = distribution.sample()
        log_probability = distribution.log_prob(action)
        action = action.item()
        return observation, action, log_probability, value


