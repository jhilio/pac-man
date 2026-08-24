import torch
import numpy as np

from src.ai.interface import NNDirectionChooser
from .network import PacmanNetwork

from ..pacmap import PacMap
from ..enums import Direction


def evaluate(pacmap:PacMap, chooser: NNDirectionChooser):
    pacmap.restart()
    score = 0
    turns = 0

    while pacmap.pacman.lives and turns < 1000:
        turns += 1
        old_score = pacmap.score
        action = chooser.choose(pacmap)
        pacmap.pacman.next_direction = action
        # same run_step logic
        while True:
            pacman = pacmap.pacman
            old_pos = pacman.pos
            pacmap.update(1 / 60)
            if pacman.pos != old_pos:
                break
        score += pacmap.score - old_score
    return score

class EvolutionTrainer:
    def __init__(
        self,
        pacmap: PacMap,
        children_count: int,
        games_per_network: int,
        mutation_strength: float=0.1,
    ):
        self.pacmap = pacmap
        self.children_count = children_count
        self.games_per_network = games_per_network
        self.mutation_strength = mutation_strength

    def train(self, start_network, generation:int) -> PacmanNetwork:
        if generation <= 0:
            return start_network
        network_pool = [start_network.mutate(self.mutation_strength) for _ in range(self.children_count)] + [start_network]
        total_scores = [0] * len(network_pool)
        for i, network in enumerate(network_pool):
            chooser = NNDirectionChooser(network)
            for j in range(self.games_per_network):
                total_scores[i] += evaluate(self.pacmap, chooser)

        best_index = total_scores.index(
            max(total_scores)
        )
        best_one = network_pool[best_index]
        best_one.save(
            f"models/generations/gen_{generation:03d}.pt"
        )
        print(
            f"generation {generation}: "
            f"best score = {total_scores[best_index] / self.games_per_network}"
        )
        return self.train(best_one, generation-1)