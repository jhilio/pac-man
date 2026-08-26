from src.ai.interface import NNDirectionChooser
from .network import PacmanNetwork
from ..pacmap import PacMap


def evaluate(pacmap: PacMap, chooser: NNDirectionChooser):
    pacmap.restart(True)
    score = 0
    turns = 0
    visited = set()
    while pacmap.pacman.lives and turns < 1000:
        turns += 1
        old_score = pacmap.score
        action = chooser.choose(pacmap)
        pacmap.pacman.next_direction = action
        # same run_step logic
        while True:
            pacman = pacmap.pacman
            old_pos = pacman.pos
            visited.add(old_pos)
            pacmap.update(1 / 60)
            if pacman.pos != old_pos:
                break
        score += pacmap.score - old_score

    scaled_score = score * len(visited) / turns
    return score, scaled_score


class EvolutionTrainer:
    def __init__(
        self,
        pacmap: PacMap,
        children_count: int,
        games_per_network: int,
        mutation_strength: float = 0.05,
    ):
        self.pacmap = pacmap
        self.children_count = children_count
        self.games_per_network = games_per_network
        self.mutation_strength = mutation_strength

    def train(
        self, start_network: list[PacmanNetwork], generation: int
    ) -> PacmanNetwork:
        if generation <= 0:
            return start_network[-1]
        network_pool = start_network + [
            start_network[-1].mutate(self.mutation_strength)
            for _ in range(self.children_count)
        ]
        total_scores = [0] * len(network_pool)
        total_scaled_scores = [0] * len(network_pool)
        for i, network in enumerate(network_pool):
            chooser = NNDirectionChooser(network)
            for j in range(self.games_per_network):
                score, scaled_score = evaluate(self.pacmap, chooser)
                total_scores[i] += score
                total_scaled_scores[i] += scaled_score
            self.pacmap.restart()

        best_index = total_scaled_scores.index(max(total_scaled_scores))
        best_one = network_pool[best_index]
        best_one.save(f"models/generations/gen_{generation:03d}.pt")
        print(
            f"generation {generation}: "
            f"best score = {total_scores[best_index] / self.games_per_network}"
        )
        with open("models/generations/logs.txt", "a+") as log:
            log.write(
                f"generation {generation:03d} : {total_scores[best_index] / self.games_per_network}\n"
            )
        return self.train([start_network[0]] + [best_one], generation - 1)
