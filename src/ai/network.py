from pathlib import Path
from typing import Self
import torch
import torch.nn as nn


class PacmanNetwork(nn.Module):

    def __init__(self, ghost_count=4,model_path=None):
        super().__init__()
        channels = 6 + ghost_count
        self.ghost_count = ghost_count
        self.cnn = nn.Sequential(
            nn.Conv2d(channels, 32, 3, padding=1),
            nn.ReLU(),
            nn.Conv2d(32, 64, 3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((4, 4)),
        )
        self.frightened = nn.Sequential(
            nn.Linear(1, 8),
            nn.ReLU(),
        )
        self.head = nn.Sequential(
            nn.Linear(
                64 * 4 * 4 + 8,
                128,
            ),
            nn.ReLU(),
            nn.Linear(128, 4),
        )
        if model_path is not None:
            self.model_path = Path(model_path)
            self.load()
        else:
            self.model_path = None

    def forward(self, observation, fright_time):
        spatial = self.cnn(observation)
        spatial = torch.flatten(spatial, 1)
        fright = self.frightened(fright_time)
        x = torch.cat(
            [spatial, fright],
            dim=1,
        )
        return self.head(x)

    def save(self, path=None):
        path = Path(path) if path else self.model_path
        if path is None:
            raise ValueError(
                "No save path provided."
            )
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        torch.save(
            self.state_dict(),
            path,
        )
        print(f"Model saved to {path.resolve()}")
    
    def load(self, path=None):
        path = Path(path) if path else self.model_path
        if path is None:
            print(
                "no path provided either in init or load",
                "using random initialization."
            )
            return
        if not path.exists():
            print(
                f"No model found at {path.resolve()}, "
                "using random initialization."
            )
            return
        print(f"Loading model from {path.resolve()}")
        state_dict = torch.load(
            path,
            weights_only=True,
        )
        self.load_state_dict(state_dict)
        print("Model loaded.")

    def mutate(self, strength=0.01):
        mutated = PacmanNetwork(
            ghost_count=self.ghost_count,
        )

        with torch.no_grad():
            for parameter, mutated_parameter in zip(
                self.parameters(),
                mutated.parameters(),
            ):
                mutated_parameter.copy_(
                    parameter
                    + torch.randn_like(parameter) * strength
                )

        return mutated

    def compare(self, other: Self):
        for name, parameter in self.named_parameters():
            other_parameter = dict(
                other.named_parameters()
            )[name]

            difference = (
                parameter.detach() - other_parameter.detach()
            ).abs().max().item()

            if difference != 0:
                print(
                    f"{name}: max difference = {difference}"
                )