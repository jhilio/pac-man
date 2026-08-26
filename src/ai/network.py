from pathlib import Path
from typing import Self
import torch
import torch.nn as nn


class PacmanNetwork(nn.Module):

    def __init__(self, ghost_count=4, model_path=None):
        super().__init__()
        channels = 6 + ghost_count
        self.ghost_count = ghost_count
        # =========================================
        # Feature extractor
        # =========================================
        self.cnn = nn.Sequential(
            nn.Conv2d(
                channels,
                32,
                3,
                padding=1,
            ),
            nn.ReLU(),
            nn.Conv2d(
                32,
                64,
                3,
                padding=1,
            ),
            nn.ReLU(),
            nn.Conv2d(
                64,
                64,
                3,
                padding=1,
            ),
            nn.ReLU(),
        )
        # =========================================
        # Local action information
        # =========================================
        self.action_map = nn.Conv2d(
            64,
            4,
            kernel_size=1,
        )
        # =========================================
        # Global information
        # =========================================
        self.global_pool = nn.AdaptiveAvgPool2d(1)
        self.global_head = nn.Sequential(
            nn.Linear(64, 32),
            nn.ReLU(),
        )
        # =========================================
        # Frightened information
        # =========================================
        self.frightened = nn.Sequential(
            nn.Linear(1, 8),
            nn.ReLU(),
        )
        # =========================================
        # Final decision
        # =========================================
        self.head = nn.Sequential(
            nn.Linear(
                4 + 32 + 8,
                64,
            ),
            nn.ReLU(),
            nn.Linear(
                64,
                4,
            ),
        )
        if model_path is not None:
            self.model_path = Path(model_path)
            self.load()
        else:
            self.model_path = None

    def forward(
        self,
        observation,
        fright_time,
        pacman_position,
    ):
        features = self.cnn(observation)
        # -----------------------------------------
        # Local information
        # -----------------------------------------
        action_map = self.action_map(features)
        x, y = pacman_position
        local = action_map[:, :, x, y]
        # -----------------------------------------
        # Global information
        # -----------------------------------------
        global_features = self.global_pool(features)
        global_features = torch.flatten(
            global_features,
            1,
        )
        global_features = self.global_head(global_features)
        # -----------------------------------------
        # Frightened information
        # -----------------------------------------
        frightened = self.frightened(fright_time)
        # -----------------------------------------
        # Combine everything
        # -----------------------------------------
        combined = torch.cat(
            [
                local,
                global_features,
                frightened,
            ],
            dim=1,
        )
        return self.head(combined)

    def save(self, path=None):
        path = Path(path) if path else self.model_path
        if path is None:
            raise ValueError("No save path provided.")
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
                "using random initialization.",
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
                    parameter + torch.randn_like(parameter) * strength
                )

        return mutated

    def compare(self, other: Self):
        for name, parameter in self.named_parameters():
            other_parameter = dict(other.named_parameters())[name]

            difference = (
                (parameter.detach() - other_parameter.detach())
                .abs()
                .max()
                .item()
            )

            if difference != 0:
                print(f"{name}: max difference = {difference}")
