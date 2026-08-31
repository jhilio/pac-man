from collections.abc import Callable
from typing import Any, Optional, Self, SupportsIndex, overload

import pygame
from pygame.surface import Surface

from ..vector import Pos2D


class CyclicList(list):
    @overload
    def __getitem__(self, k: SupportsIndex) -> Any:
        ...

    @overload
    def __getitem__(self, k: slice) -> list[Any]:
        ...

    def __getitem__(self, k: SupportsIndex | slice) -> Any | list[Any]:
        if isinstance(k, int):
            k %= len(self)
        return super().__getitem__(k)


class PercentRect:
    def __init__(self, x: float, y: float, width: float, height: float):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def to_rect(self, screen: Surface) -> pygame.Rect:
        screen_width, screen_height = screen.get_size()
        return pygame.Rect(
            int(self.x * screen_width),
            int(self.y * screen_height),
            int(self.width * screen_width),
            int(self.height * screen_height),
        )


class DelayedCall:
    def __init__(self, func: Callable, *args: Any, **kwargs: Any):
        self.func = func
        self.args = tuple(args)
        self.kwargs = dict(kwargs) if kwargs else {}

    def __call__(self) -> Any:
        if not callable(self.func):
            raise ValueError("DelayedCall with a non callable func")
        return self.func(*self.args, **self.kwargs)


class ClickableButton:
    def __init__(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        screen: Surface,
        font: pygame.font.Font,
        effect: Optional[DelayedCall] = None,
        text: str | DelayedCall = "",
        image: Optional[Surface] = None,
        hovered_image: Optional[Surface] = None,
    ):
        self.percent_rect = PercentRect(x, y, width, height)
        self.font = font
        self.effect = effect
        self.screen = screen
        self._text = text
        self._image = image
        self._hovered_image = hovered_image
        self.is_hovered = False

    def update(self, dt: float, is_hovered: bool = False) -> None:
        self.is_hovered = is_hovered

    def is_in(self, pos: Pos2D) -> bool:
        return self.to_screen_rect.collidepoint(*pos)

    def on_click(self) -> None:
        if self.effect:
            self.effect()

    @property
    def text(self) -> str:
        if isinstance(self._text, str):
            return self._text
        res = self._text()
        if isinstance(res, str):
            return res
        raise TypeError(f"text generator for button returned {type(res)}")

    @property
    def to_screen_rect(self) -> pygame.Rect:
        return self.percent_rect.to_rect(self.screen)

    @property
    def image(self) -> pygame.Surface:
        if self._hovered_image and self.is_hovered:
            surface = pygame.transform.scale(
                self._hovered_image, tuple(self.to_screen_rect)[2:]
            )
        elif self._image:
            surface = pygame.transform.scale(
                self._image, tuple(self.to_screen_rect)[2:]
            )
        else:
            surface = pygame.Surface(tuple(self.to_screen_rect)[2:])
        txt = self.text
        if txt:
            lines = self.text.split("\n")
            surface_lines: list[Surface] = []
            for i, line in enumerate(lines):
                surface_lines.append(
                    self.font.render(line, True, (255, 255, 255))
                )

            width = max(a.get_width() for a in surface_lines)
            height = (self.font.get_height() + 2) * len(surface_lines)
            start = Pos2D(surface.get_size()) / 2 - (Pos2D(width, height) / 2)

            for i, line2 in enumerate(surface_lines):
                surface.blit(
                    line2, start + Pos2D(0, ((self.font.get_height() + 2) * i))
                )
        return surface


class AnimatedButton(ClickableButton):
    last_hovered: Optional["AnimatedButton"] = None
    anim_launched: bool = False

    def __init__(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        screen: Surface,
        font: pygame.font.Font,
        *args: Any,
        effect: Optional[DelayedCall] = None,
        text: str | DelayedCall = "",
        image: Optional[pygame.Surface] = None,
        hovered_image: Optional[Surface] = None,
        on_hover: Optional[Callable[[Self], None]] = None,
        animation_image: Optional[CyclicList] = None,
        animation_frames_count: int = 5,
        animate_func: Optional[Callable[[
            Self, Surface], Surface]] = None,
        anim_duration: float = 1.0,
    ):
        super().__init__(
            x,
            y,
            width,
            height,
            screen,
            font,
            effect,
            text,
            image,
            hovered_image,
        )
        self._on_hover: Callable[[Any], None] = (
            on_hover if on_hover is not None else self.default_hover
        )
        self._animate_func: Callable[[Any, Surface], Surface] = (
            animate_func
            if animate_func is not None
            else self.default_animate
        )
        self.anim_duration = anim_duration
        self.animation_image = animation_image
        self.anim_stage: Optional[float] = None
        self.animation_frames_count = animation_frames_count
        self.extra = args

    @staticmethod
    def default_hover(button: Any) -> None:
        pass

    @staticmethod
    def default_animate(
            button: Any, base_image: Surface) -> Surface:
        return base_image

    def on_click(self) -> None:
        if not self.__class__.anim_launched:
            if self.anim_duration:
                self.anim_stage = 1.0
                self.__class__.anim_launched = True
            elif self.effect:
                self.effect()

    def update(self, dt: float, is_hovered: bool = False) -> None:
        super().update(dt, is_hovered)
        if self.anim_stage is not None:
            self.anim_stage -= dt / self.anim_duration
            if self.anim_stage <= 0:
                self.anim_stage = None
                self.__class__.anim_launched = False
                if self.effect:
                    self.effect()

    @property
    def image(self) -> Surface:
        if self.is_hovered:
            self._on_hover(self)
        base_image = super().image
        animated = self._animate_func(self, base_image)
        return pygame.transform.scale(animated, tuple(self.to_screen_rect)[2:])


def pac_button_hover(self: AnimatedButton) -> None:
    self.__class__.last_hovered = self


def pac_button_anim(
    self: Any, base_image: Surface
) -> Surface:
    if self.animation_image is not None and self.anim_stage is not None:
        anim_frame = self.animation_image[
            int(self.anim_stage * self.animation_frames_count)
        ]
        x = (base_image.get_width() - anim_frame.get_width()) * self.anim_stage
        x = x * 0.9 + 5
        y = base_image.get_height() / 2 - anim_frame.get_height() / 2
        new = base_image.copy()
        new.blit(
            anim_frame,
            (x, y),
        )
        return new
    elif (
        self.animation_image is not None
        and self.__class__.last_hovered is self
        and not self.__class__.anim_launched
    ):
        anim_frame = self.animation_image[0]
        x = base_image.get_width() - anim_frame.get_width()
        x = x * 0.9 + 5
        y = base_image.get_height() / 2 - anim_frame.get_height() / 2
        new = base_image.copy()
        new.blit(anim_frame, (x, y))
        return new
    return base_image


def paused_anim(
    self: Any, base_image: Surface
) -> Surface:
    if self.animation_image is None:
        raise ValueError("need animation images for this animation")
    if self.extra[0].paused:
        ret: Surface = self.animation_image[1]
    else:
        ret = self.animation_image[0]
    return ret
