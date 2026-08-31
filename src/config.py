from __future__ import annotations
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from .pacmap import PacMap
from typing import Optional, Any
import pygame


class Level(TypedDict):
    frightened_duration: int
    ghost_speed: int
    ghost_fright_speed: int
    pacman_speed: int
    pacman_fright_speed: int
    duration: int
    phases: list[list[str | None | int]]


class Config(TypedDict):
    pacgum_proportion: float
    lives: int
    seed: int
    width: int
    height: int
    points_per_pacgum: int
    points_per_super_pacgum: int
    points_per_ghost: int
    levels: dict[str, Level]


class AssetsManager:
    def __init__(self):
        self._originals: dict[str, pygame.Surface] = {}
        self.scaled = {}

    def load(
        self, name: str, path: str, color_key: Optional[pygame.Color] = None
    ) -> Any | pygame.Surface:
        image = pygame.image.load(path)
        if color_key is not None:
            image.set_colorkey(color_key)
        self._originals[name] = image
        return self.get_asset(name)

    def get_asset(
        self,
        name: str,
        scaled_size: Optional[tuple[int, int]] = None,
        size_multiplier: float = 1,
        scaling: bool = True,
    ) -> Any | pygame.Surface:
        if scaled_size is None:
            x = y = MainData.cell_size * size_multiplier
        else:
            x, y = scaled_size
        hashable = (name, x, y, size_multiplier, scaling)
        if self.scaled.get((x, y)) is None:
            self.scaled[(x, y)] = {}
        cache = self.scaled[(x, y)]
        if hashable in cache:
            return cache[hashable]
        unscaled = self._originals.get(name)
        if unscaled is None:
            raise ValueError(f"asset {name} wansnt loaded")
        if not scaling:
            return unscaled
        scaled = pygame.transform.scale(
            unscaled, (x * size_multiplier, y * size_multiplier)
        )
        if unscaled.get_colorkey() is not None:
            scaled.set_colorkey(unscaled.get_colorkey()[:3])
        cache[hashable] = scaled
        return scaled


class MainData:
    tick_rate = 10
    cell_size = 16
    high_scores = {}
    config_from_file = Config()
    assets = AssetsManager()
    pacmap: Optional[PacMap] = None
