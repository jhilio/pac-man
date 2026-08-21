from ctypes.wintypes import HHOOK

import pygame
from typing import Callable, Optional
from .vector import Pos2D
from .config import MainData

class PercentRect:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def to_rect(self, screen):
        screen_width, screen_height = screen.get_size()

        return pygame.Rect(
            int(self.x * screen_width),
            int(self.y * screen_height),
            int(self.width * screen_width),
            int(self.height * screen_height),
        )


class DelayedCall:
    def __init__(self, func: Callable, *args, **kwargs):
        self.call = {
            "function": func,
            "args": tuple(args),
            "kwargs": dict(kwargs) if kwargs else {},
        }

    def __call__(self):
        if not callable(self.call.get("function")):
            raise ValueError(f"DelayedCall with a non callable func")
        func, args, kwargs = self.call.values()

        func(*args, **kwargs)




class ClickableButton:
    def __init__(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        screen: pygame.Surface,
        effect: Optional[DelayedCall] = None,
        text: str = "",
        font_size: Optional[int] = None,
        image: Optional[pygame.Surface]=None,
        hovered_image: Optional[pygame.Surface]=None
    ):
        self.percent_rect =PercentRect(x, y, width, height)
        self.effect = effect
        self.screen = screen
        self.text = text
        self.font_size = font_size
        self.__image = image
        self.__hovered_image = hovered_image

    def is_in(self, pos: Pos2D):
        return self.to_screen_rect.collidepoint(*pos)

    def on_click(self):
        if self.effect:
            self.effect()

    @property
    def to_screen_rect(self):
        return self.percent_rect.to_rect(self.screen)

    @property
    def image(self):
        if self.__image:
            return pygame.transform.scale(self.__image, tuple(self.to_screen_rect)[2:])
        surface = pygame.Surface(tuple(self.to_screen_rect)[2:])
        return surface

    @property
    def hovered_image(self):
        if self.__hovered_image:
            return pygame.transform.scale(self.__hovered_image, tuple(self.to_screen_rect)[2:])
        if self.__image:
            return pygame.transform.scale(self.__image, tuple(self.to_screen_rect)[2:])
        surface = pygame.Surface(tuple(self.to_screen_rect)[2:])
        return surface

