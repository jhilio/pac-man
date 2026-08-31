from pathlib import Path
from typing import Optional, Self

import numpy
import torch
from torch import nn


class PacmanNetwork(nn.Module):

    def __init__(
            self,
            ghost_count: int = 4,
            model_path: Optional[Path] = None
    ):
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
            self.model_path: Optional[Path] = Path(model_path)
            self.load()
        else:
            self.model_path = None

    def forward(
        self,
        observation: numpy.ndarray,
        fright_time: float,
        pacman_position: tuple[int, int],
    ) -> torch.Tensor:
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
        output: torch.Tensor = self.head(combined)
        return output

    def save(self, path: Optional[str] = None) -> None:
        real_path = Path(path) if path else self.model_path
        if real_path is None:
            raise ValueError("No save path provided.")
            return
        real_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        torch.save(
            self.state_dict(),
            real_path,
        )
        print(f"Model saved to {real_path.resolve()}")

    def load(self, path: Optional[str] = None) -> None:
        real_path = Path(path) if path else self.model_path
        if real_path is None:
            print(
                "no path provided either in init or load",
                "using random initialization.",
            )
            return
        if not real_path.exists():
            print(
                f"No model found at {real_path.resolve()}, "
                "using random initialization."
            )
            return
        print(f"Loading model from {real_path.resolve()}")
        state_dict = torch.load(
            real_path,
            weights_only=True,
        )
        self.load_state_dict(state_dict)
        print("Model loaded.")

    def mutate(self, strength: float = 0.01) -> "PacmanNetwork":
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

    def compare(self, other: Self) -> None:
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
