from pathlib import Path
import torch
import torch.nn as nn


class PacmanNetwork(nn.Module):
    def __init__(
        self,
        ghost_count=4,
        model_path="models/pacman.pt",
    ):
        super().__init__()

        self.model_path = Path(model_path)

        channels = 6 + ghost_count

        self.cnn = nn.Sequential(
            nn.Conv2d(channels, 32, 3, padding=1),
            nn.ReLU(),
            nn.Conv2d(32, 64, 3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((1, 1)),
        )

        self.policy = nn.Linear(64, 4)
        self.value = nn.Linear(64, 1)

        self.load()

    def save(self, verbose=False):
        self.model_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        torch.save(
            self.state_dict(),
            self.model_path,
        )
        if verbose:
            print(f"Model saved to {self.model_path.resolve()}")

    def save_extern(self, name:str,verbose=False):
        extern_path = (
            self.model_path.parent
            / f"{name}.pt"
        )

        extern_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        torch.save(
            self.state_dict(),
            extern_path,
        )
        if verbose:
            print(f"Model saved to {extern_path.resolve()}")

    def load(self, verbose= False):
        if not self.model_path.exists():
            print(
                f"No model found at "
                f"{self.model_path.resolve()}, "
                f"using random initialization."
            )
            return
        if verbose:
            print(f"Loading model from {self.model_path.resolve()}")

        state_dict = torch.load(
            self.model_path,
            weights_only=True,
        )

        self.load_state_dict(state_dict)
        if verbose:
            print("Model loaded.")

    def compare_nn(self, other):
        """
        Compare this network with another network.

        Returns True if every parameter is exactly identical.
        Also prints the maximum absolute difference for each parameter.
        """

        same = True

        for (name_a, param_a), (name_b, param_b) in zip(
            self.named_parameters(),
            other.named_parameters(),
        ):
            if name_a != name_b:
                print(
                    f"Different parameter names: "
                    f"{name_a} != {name_b}"
                )
                same = False
                continue

            difference = (
                param_a.detach() - param_b.detach()
            ).abs().max().item()

            identical = difference == 0.0

            print(
                f"{name_a}: "
                f"max_difference={difference:.10g} "
                f"same={identical}"
            )

            if not identical:
                same = False

        print(
            "Networks identical:"
            f" {same}"
        )

        return same

    def forward(self, observation):
        x = self.cnn(observation)
        x = torch.flatten(x, 1)

        policy = self.policy(x)
        value = self.value(x)

        return policy, value
