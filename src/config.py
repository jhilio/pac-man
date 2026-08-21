from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .pacmap import PacMap
from typing import Optional, Any
import pygame


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
        self, name: str, scaled_size:Optional[int]=None,size_multiplier: float = 1, scaling: bool = True
    ) -> Any | pygame.Surface:
        if scaled_size:
            size = scaled_size
        else:
            size = MainData.cell_size * size_multiplier
        hashable = (name, size_multiplier, scaling)
        if self.scaled.get(size) is None:
            self.scaled[size] = {}
        cache = self.scaled[size]
        if hashable in cache:
            return cache[hashable]
        unscaled = self._originals.get(name)
        if unscaled is None:
            raise ValueError(f"asset {name} wansnt loaded")
        if not scaling:
            return unscaled
        scaled = pygame.transform.scale(
            unscaled, (size * size_multiplier, size * size_multiplier)
        )
        if unscaled.get_colorkey() is not None:
            scaled.set_colorkey(unscaled.get_colorkey()[:3])
        cache[hashable] = scaled
        return scaled


class MainData:
    tick_rate = 10
    cell_size = 16
    high_scores = {}
    config_from_file = {}
    assets = AssetsManager()
    pacmap: Optional[PacMap] = None
