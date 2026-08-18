from __future__ import annotations
from typing import Optional
import pygame





class AssetsManager:
    def __init__(self):
        self._originals: dict[str, pygame.Surface]= {}
        self.scaled = {}


    def load(self, name:str, path:str, color_key: Optional[pygame.Color]=None):
        image= pygame.image.load(path)
        if color_key is not None:
            image.set_colorkey(color_key)
        self._originals[name] = image 
        return self.get_asset(name)


    def get_asset(self, name:str, size_multiplier:int = 1):
        size=Config.cell_size * size_multiplier
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
        if unscaled.get_colorkey() is not None:
            scaled.set_colorkey(unscaled.get_colorkey()[:3])
        cache[name] = scaled
        return scaled

class Config:
    cell_size = 16
    config_from_file = {}
    assets = AssetsManager()
