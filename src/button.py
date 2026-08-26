import pygame
from typing import Callable, Optional, Any

from .vector import Pos2D


class CyclicList(list):
    def __getitem__(self, s):
        if isinstance(s, int):
            s %= len(self)
        return super().__getitem__(s)


class PercentRect:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def to_rect(self, screen) -> pygame.Rect:
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

    def __call__(self) -> Any:
        if not callable(self.call.get("function")):
            raise ValueError("DelayedCall with a non callable func")
        func, args, kwargs = self.call.values()

        return func(*args, **kwargs)


class ClickableButton:
    def __init__(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        screen: pygame.Surface,
        effect: Optional[DelayedCall] = None,
        text: str | DelayedCall = "",
        font_size: Optional[int] = None,
        image: Optional[pygame.Surface] = None,
        hovered_image: Optional[pygame.Surface] = None,
    ):
        self.percent_rect = PercentRect(x, y, width, height)
        self.effect = effect
        self.screen = screen
        self._text = text
        self.font_size = font_size
        self._image = image
        self._hovered_image = hovered_image

    def is_in(self, pos: Pos2D) -> Any:
        return self.to_screen_rect.collidepoint(*pos)

    def on_click(self) -> None:
        if self.effect:
            self.effect()

    @property
    def text(self) -> str:
        if isinstance(self._text, str):
            return self._text
        return self._text()

    @property
    def to_screen_rect(self) -> pygame.Rect:
        return self.percent_rect.to_rect(self.screen)

    @property
    def image(self) -> pygame.Surface:
        if self._image:
            return pygame.transform.scale(
                self._image, tuple(self.to_screen_rect)[2:]
            )
        surface = pygame.Surface(tuple(self.to_screen_rect)[2:])
        return surface

    @property
    def hovered_image(self) -> pygame.Surface:
        if self._hovered_image:
            return pygame.transform.scale(
                self._hovered_image, tuple(self.to_screen_rect)[2:]
            )
        if self._image:
            return pygame.transform.scale(
                self._image, tuple(self.to_screen_rect)[2:]
            )
        surface = pygame.Surface(tuple(self.to_screen_rect)[2:])
        return surface


class AnimatedButton(ClickableButton):
    last_hovered = None
    anim_launched = False

    def __init__(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        screen: pygame.Surface,
        effect: Optional[DelayedCall] = None,
        text: str | DelayedCall = "",
        font_size: Optional[int] = None,
        image: Optional[pygame.Surface] = None,
        hovered_image: Optional[pygame.Surface] = None,
        on_hover=None,
        animation_image: Optional[CyclicList[pygame.surface.Surface]] = None,
        animation_frames_count: int = 5,
        animate_func: Optional[DelayedCall] = None,
        anim_duration=1,
    ):
        super().__init__(
            x,
            y,
            width,
            height,
            screen,
            effect,
            text,
            font_size,
            image,
            hovered_image,
        )
        self._on_hover = (
            on_hover if on_hover is not None else self.__class__.default_hover
        )
        self._animate_func = (
            animate_func
            if animate_func is not None
            else self.__class__.default_animate
        )
        self.anim_duration = anim_duration
        self.animation_image = animation_image
        self.anim_stage = None
        self.animation_frames_count = animation_frames_count

    def default_hover(self):
        self.__class__.last_hovered = self

    def on_click(self) -> None:
        if not self.__class__.anim_launched:
            self.anim_stage = 1
            self.__class__.anim_launched = True

    def update(self, dt: float):
        if self.anim_stage:
            self.anim_stage -= dt / self.anim_duration
            if self.anim_stage < 0:
                self.anim_stage = None
                self.__class__.anim_launched = False
                if self.effect:
                    self.effect()

    def default_animate(self, base_image: pygame.surface.Surface):
        if self.animation_image is not None and self.anim_stage is not None:
            anim_frame = self.animation_image[
                int(self.anim_stage * self.animation_frames_count)
            ]
            x = (
                base_image.get_width() - anim_frame.get_width()
            ) * self.anim_stage
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

    @property
    def image(self):
        base_image = super().image
        return self._animate_func(self, base_image)

    @property
    def hovered_image(self) -> pygame.Surface:
        self._on_hover(self)
        return self.image
