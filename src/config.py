from __future__ import annotations
import pygame





class AssetsManager:
    def __init__(self):
        self._originals: dict[str, pygame.Surface]= {}
        self.scaled = {}


    def load(self, name:str, path:str, color_key: Optional[pygame.Color]=None):
        self._originals[name] = pygame.image.load(path)
        if color_key:
            self._originals[name].set_colorkey(color_key)
        return self.get_asset(name)


    def get_asset(self, name:str, size_multiplier:int = 1):
        size=Config.cell_size
        if self.scaled.get(size) is None:
            self.scaled[size] = {}
        cache = self.scaled[size]
        if name in cache:
            return cache[name]
        unscaled = self._originals.get(name)
        if unscaled is None:
            raise ValueError(f"asset {name} wansnt loaded")
        print("miss")
        scaled = pygame.transform.scale(unscaled, (size*size_multiplier, size*size_multiplier))
        cache[name] = scaled
        return scaled

class Config:
    cell_size = 16
    config_from_file = {}
    assets = AssetsManager()
