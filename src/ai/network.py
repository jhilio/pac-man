import os
import torch
import torch.nn as nn

class PacmanNetwork(nn.Module):
    def __init__(self, ghost_count=4, model_path="models/pacman.pt"):
        super().__init__()

        self.model_path = model_path
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

    def save(self):
        torch.save(self.state_dict(), self.model_path)

    def load(self):
        if os.path.exists(self.model_path):
            self.load_state_dict(
                torch.load(self.model_path, weights_only=True)
            )

    def forward(self, observation):
        x = self.cnn(observation)
        x = torch.flatten(x, 1)

        policy = self.policy(x)
        value = self.value(x)

        return policy, value

