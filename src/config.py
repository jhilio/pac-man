from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Generic, TypedDict, TypeVar

from pygame.surface import Surface

if TYPE_CHECKING:
    from .pacmap import PacMap
from typing import Any, Optional

import pygame


class Level(TypedDict):
    frightened_duration: int
    ghost_speed: int
    ghost_fright_speed: int
    pacman_speed: int
    pacman_fright_speed: int
    duration: int
    phases: list[list[str | None | int]]


levels: list[Level] = (
    [
        Level(
            frightened_duration=5,
            ghost_speed=75,
            ghost_fright_speed=50,
            pacman_speed=80,
            pacman_fright_speed=90,
            duration=90,
            phases=[
                ["scatter", 7],
                ["chase", 20],
                ["scatter", 7],
                ["chase", 20],
                ["scatter", 5],
                ["chase", 20],
                ["scatter", 5],
                ["chase", None],
            ],
        )
    ]
    + [
        Level(
            frightened_duration=5,
            ghost_speed=85,
            ghost_fright_speed=55,
            pacman_speed=90,
            pacman_fright_speed=95,
            duration=90,
            phases=[
                ["scatter", 7],
                ["chase", 20],
                ["scatter", 7],
                ["chase", 20],
                ["scatter", 5],
                ["chase", 1033],
                ["scatter", 1],
                ["chase", None],
            ],
        )
        for _ in range(3)
    ]
    + [
        Level(
            frightened_duration=5,
            ghost_speed=95,
            ghost_fright_speed=60,
            pacman_speed=100,
            pacman_fright_speed=100,
            duration=90,
            phases=[
                ["scatter", 5],
                ["chase", 20],
                ["scatter", 5],
                ["chase", 20],
                ["scatter", 5],
                ["chase", 1033],
                ["scatter", 1],
                ["chase", None],
            ],
        )
        for _ in range(16)
    ]
)


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


levels_dict = {
    str(i): level for i, level in enumerate(levels, 1)
}

DEFAULT_CONFIG = Config(
    pacgum_proportion=0.5,
    lives=3,
    seed=0,
    width=15,
    height=15,
    points_per_pacgum=10,
    points_per_super_pacgum=50,
    points_per_ghost=50,
    levels=levels_dict,
)


class AssetsManager:
    def __init__(self) -> None:
        self._originals: dict[str, Surface] = {}
        self.scaled: dict[
            tuple[int | float, int | float],
            dict[tuple[str, float, float, float, float], Surface]] = {}

    def load(
        self, name: str, path: str, color_key: Optional[pygame.Color] = None
    ) -> Surface:
        """load an asset into the asset manager
        Args:
            name (str): name of the asset
            path (str): full path to the asset
            color_key (Optional[pygame.Color], optional):
                optional colorkey to set to the asset.
                Defaults to None.
        Returns:
            Surface: the loaded asset
        """
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
    ) -> Surface:
        """search trough the cache if the asset is present with this size,
        if not scale it,
        add it to cache, then return it
        Args:
            name (str): name of the asset
            scaled_size (Optional[tuple[int, int]], optional):
              size asked. Defaults to None.
            size_multiplier (float, optional):
                multiplier over scaled_size.
                Defaults to 1.
            scaling (bool, optional):
                completely desactivate scaling.
                Defaults to True.
        Raises:
            ValueError: if the asset asked isnt loaded
        Returns:
            Surface: the loaded then scaled asset
        """
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
        color_key = unscaled.get_colorkey()
        if color_key is not None:
            scaled.set_colorkey(color_key[:3])
        cache[hashable] = scaled
        return scaled


T = TypeVar("T")


class ClassProperty(Generic[T]):
    """used to create a property so that typechecker
    can see that MainData.pacmap is either a PacMap
    Args:
        Generic (_type_): which type will be returned
    """
    def __init__(self, getter: Callable[[Any], T]):
        self.getter = getter

    def __get__(self, instance: None, owner: Any) -> T:
        return self.getter(owner)


class MainData:
    tick_rate = 10
    cell_size = 16
    high_scores: dict[str, int] = {}
    config_from_file = DEFAULT_CONFIG
    assets = AssetsManager()

    _pacmap: PacMap | None = None

    @ClassProperty
    def pacmap(cls) -> PacMap:
        """get the current pacmap
        Raises:
            RuntimeError: if no pacmap has been set
        Returns:
            PacMap: the current pacmap
        """
        if cls._pacmap is None:
            raise RuntimeError("MainData.pacmap has not been initialized")
        return cls._pacmap

    @classmethod
    def set_pacmap(cls, pacmap: PacMap) -> None:
        """small setter for self.pacmap
        Args:
            pacmap (PacMap): new PacMap
        """
        cls._pacmap = pacmap
