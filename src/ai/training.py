import torch
import numpy as np
from ..enums import Direction
from dataclasses import dataclass

@dataclass
class Experience:
    observation: np.ndarray
    action: int
    log_probability: torch.Tensor
    value: torch.Tensor
    reward: float




class Trainer:
    def __init__(self, pacmap, chooser):
        self.pacmap = pacmap
        self.chooser = chooser
        self.optimizer = torch.optim.Adam(
            self.chooser.network.parameters(),
            lr=3e-2,
        )

    def loop(self):
        turn = 0
        list_experiences = []
        reward_total = 0
        last_life_amount = self.pacmap.pacman.lives
        while self.pacmap.pacman.lives and turn < 1000:
            turn +=1
            old_score = self.pacmap.score

            observation, action, log_probability, value = self.chooser.choose_training(self.pacmap)
            self.pacmap.pacman.next_direction = Direction(1 << action)
            self.run_step()
            reward = self.pacmap.score - old_score
            reward -= 0.2
            if self.pacmap.pacman.lives != last_life_amount:
                reward -= reward_total // 4
                last_life_amount = self.pacmap.pacman.lives
            reward_total += reward
            list_experiences.append(Experience(
                observation,
                action,
                log_probability.detach(),
                value.detach(),
                reward,
            ))
        return list_experiences, self.pacmap.score

    def run_step(self):
        while True:
            pacman = self.pacmap.pacman
            prec_pos = pacman.pos
            self.pacmap.update(1/60)
            if pacman.pos % (3, 3) == (1, 1) and pacman.pos != prec_pos:
                break
    
    def calculate_returns(self, experiences, gamma=0.99):
        returns = []
        running_return = 0.0

        for experience in reversed(experiences):
            running_return = (
                experience.reward
                + gamma * running_return
            )
            returns.append(running_return)

        returns.reverse()

        return torch.tensor(returns, dtype=torch.float32) 



    def train(self, experiences: list[Experience]):
        observations = torch.from_numpy(
            np.stack([e.observation for e in experiences])
        )
        actions = torch.tensor(
            [e.action for e in experiences],
            dtype=torch.long,
        )
        # These belong to the policy that generated the experiences.
        old_log_probs = torch.stack(
            [e.log_probability for e in experiences]
        ).detach().squeeze(-1)
        # Calculate these once from the rollout.
        returns = self.calculate_returns(experiences)
        old_values = torch.tensor(
            [e.value.item() for e in experiences],
            dtype=torch.float32,
        )
        advantages = returns - old_values
        advantages = (
            advantages - advantages.mean()
        ) / (
            advantages.std() + 1e-8
        )
        clip_epsilon = 0.2
        value_coefficient = 0.5
        for epoch in range(4):
            # Evaluate the CURRENT network.
            logits, values = self.chooser.network(observations)

            logits = self.chooser._mask_walls(
                logits,
                observations,
            )

            distribution = torch.distributions.Categorical(
                logits=logits
            )

            new_log_probs = distribution.log_prob(actions)

            # Compare current policy to the OLD policy.
            ratio = torch.exp(
                new_log_probs - old_log_probs
            )

            # PPO clipped objective.
            policy_objective = ratio * advantages

            clipped_ratio = torch.clamp(
                ratio,
                1 - clip_epsilon,
                1 + clip_epsilon,
            )

            clipped_objective = (
                clipped_ratio * advantages
            )

            objective = torch.min(
                policy_objective,
                clipped_objective,
            )

            policy_loss = -objective.mean()

            # Value loss uses the CURRENT value predictions.
            value_loss = torch.nn.functional.mse_loss(
                values.squeeze(-1),
                returns,
            )

            loss = (
                policy_loss
                + value_coefficient * value_loss
            )

            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()

    def old_train(self, experiences: list[Experience]):
        observations = torch.from_numpy(
            np.stack([e.observation for e in experiences])
        )
        actions = torch.tensor(
            [e.action for e in experiences],
            dtype=torch.long,
        )
        old_log_probs = torch.stack(
            [e.log_probability for e in experiences]
        ).detach().squeeze(-1)

        
        logits, values = self.chooser.network(observations)
        logits = self.chooser._mask_walls(logits, observations)
        distribution = torch.distributions.Categorical(logits=logits)
        new_log_probs = distribution.log_prob(actions)
        ratio = torch.exp(new_log_probs - old_log_probs)
        print(
            f"ratio: "
            f"mean={ratio.mean().item():.6f}, "
            f"std={ratio.std().item():.6f}, "
            f"min={ratio.min().item():.6f}, "
            f"max={ratio.max().item():.6f}",
        )
        returns = self.calculate_returns(experiences)
        advantages = returns - values.detach().squeeze(-1)
        
        advantages = (
            advantages - advantages.mean()
        ) / (
            advantages.std() + 1e-8
        )
        policy_objective = ratio * advantages
        clip_epsilon = 0.2

        clipped_ratio = torch.clamp(
            ratio,
            1 - clip_epsilon,
            1 + clip_epsilon,
        )
        clipped_objective = clipped_ratio * advantages
        objective = torch.min(
            policy_objective,
            clipped_objective,
        )
        policy_loss = -objective.mean()
        value_loss = torch.nn.functional.mse_loss(
            values.squeeze(-1),
            returns,
        )
        value_coefficient = 0.5
        loss = policy_loss + value_coefficient * value_loss
        self.optimizer.zero_grad()
        loss.backward()
        for name, parameter in self.chooser.network.named_parameters():
            if parameter.grad is not None:
                print(
                    name,
                    "gradient:",
                    parameter.grad.abs().mean().item()
                )
        self.optimizer.step()
        print(
            f"policy={policy_loss.item():.2f}",
            f"value={value_loss.item():.2f}",
            f"total={loss.item():.2f}",
            sep="\n",
        )

        print(
            f"advantage: "
            f"mean={advantages.mean().item():.2f}, "
            f"std={advantages.std().item():.2f}, "
            f"min={advantages.min().item():.2f}, "
            f"max={advantages.max().item():.2f}",
        )
    
