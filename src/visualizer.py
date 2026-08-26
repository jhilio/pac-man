from __future__ import annotations
import json
from unittest import result
import pygame
from typing import Optional

from src.ai.interface import NNDirectionChooser
from .vector import Pos2D
from .charachters.ghost import get_ghost_state
from .charachters.moving_entity import MovingEntities
from .pacmap import PacMap
from .enums import Direction, VisualState, AnimTypes
from .config import MainData

from .button import ClickableButton, DelayedCall, AnimatedButton, CyclicList


class Visualizer:
    Counter = 0
    CELL_MARGIN = 2

    def __init__(
        self,
        pacmap: PacMap,
        size: tuple[int, int] = (1000, 700),
        verbose: bool = False,
        nn: NNDirectionChooser = None,
    ):
        pygame.init()
        self.size = size
        self.fps = 60
        self.visualiser_state = VisualState.MAIN_MENU
        self.paused = False

        self.autoplay = True
        game_size = (
            Pos2D(
                MainData.config_from_file["width"],
                MainData.config_from_file["height"],
            )
            * MainData.cell_size
            * 3
        ) // 1
        self.game_space = pygame.Surface(game_size)
        self.pacmap = pacmap
        self.base_font_size = 13
        self.font_cache: dict[int, pygame.font.Font] = {}
        self.screen = pygame.display.set_mode(size, pygame.RESIZABLE)
        self.code_sequence = []
        self.verbose = verbose
        self.init_button()
        bg = MainData.assets.get_asset("BGmenu.jpg", scaling=False)
        bgleft = MainData.assets.get_asset("leftbg.png", scaling=False)
        bggame = MainData.assets.get_asset("gameback.jpg", scaling=False)

        self.surface_per_menu = {
            VisualState.MAIN_MENU: self.screen.copy(),
            VisualState.CONFIG: self.screen.copy(),
            VisualState.HIGH_SCORE_MENU: self.screen.copy(),
            VisualState.IN_GAME: self.screen.copy(),
            "final_buffer": self.screen.copy(),
        }
        self.background_per_menu = {
            VisualState.CONFIG: bg,
            VisualState.HIGH_SCORE_MENU: bgleft,
            VisualState.MAIN_MENU: bg,
            VisualState.IN_GAME: bggame,
        }
        self.prec_state = None
        self.nn = nn

    @property
    def active_buttons(self):
        return self.buttons_per_menu.get(self.visualiser_state, [])

    def get_background(self, state: VisualState):
        bg = self.background_per_menu.get(state, None)
        if bg is not None:
            bg = pygame.transform.scale(
                bg, (self.screen.get_width(), self.screen.get_height())
            )
        return bg

    def change_state(
        self,
        new: VisualState,
        anim_duration=0,
        anim_type=AnimTypes.LEFT_TO_RIGHT,
    ):
        if new == VisualState.IN_GAME and self.pacmap.is_finished:
            self.pacmap.restart()
        self.prec_state = self.visualiser_state

        self.anim_duration = max(anim_duration, 0.000001)
        self.act_anim = 1
        self.anim_type = anim_type
        self.visualiser_state = new

    def launch_loop(self) -> None:
        self.anim_duration = 1
        self.anim_type = AnimTypes.LEFT_TO_RIGHT
        self.act_anim = 0
        self.time: float = 0.0
        self.loop()

    def save_high_score(self) -> None:
        with open("high_scores.json", "w") as file:
            json.dump(MainData.high_scores, file, indent=2)

    def loop(self) -> None:
        """Main loop of the visualizer."""
        clock = pygame.time.Clock()
        pacman = self.pacmap.pacman
        prec_pos = pacman.pos
        while True:
            dt = clock.tick(self.fps) / 1000.0  # seconds since last frame
            for event in pygame.event.get():
                if self.event_handler(event) == pygame.QUIT:
                    self.pacmap.update_high_score()
                    self.save_high_score()
                    pygame.quit()
                    return
            # MainData.cell_size = min(pygame.display.get_window_size()) //
            # (min(len(self.pacmap.cells), len(self.pacmap.cells[0])) + 50)
            self.movement_scan()
            self.time += dt
            if self.visualiser_state == VisualState.IN_GAME:
                if not self.autoplay or self.nn is None:
                    self.movement_scan()
                elif self.nn is not None and pacman.pos != prec_pos:
                    self.pacmap.pacman.next_direction = self.nn.choose(
                        self.pacmap
                    )
                prec_pos = pacman.pos
                self.pacmap.update(dt)
                if self.pacmap.is_finished:
                    self.change_state(VisualState.PROMPTING_FOR_NAME)
            self.draw_dispatcher(dt)

    def draw_dispatcher(self, dt: float) -> None:
        t = self.pacmap.level["duration"] - self.pacmap.total_elapsed_time
        text = f"""
        {("fright left : "
            + format(self.pacmap.fright_time_left, ".1f")
            + "s") if self.pacmap.fright_time_left else ""}
        Time left : {t:.0f}S
        Phase state : {get_ghost_state().name} {self.pacmap.phase_timer}S
        Score: {self.pacmap.score}
        Current Level: {self.pacmap.level_num}
        lives : {self.pacmap.pacman.lives}
        cell_size : {MainData.cell_size}
        fps : {1/dt:.1f}
        anim: {self.act_anim / self.anim_duration}
        """
        actual = self.draw_to_menu(self.visualiser_state, dt)
        prec = self.draw_to_menu(self.prec_state, dt)

        print(self.prec_state, prec, actual)
        finish_result = self.anim_transition(actual, prec, dt)
        self.screen.blit(finish_result, (0, 0))
        if self.pacmap.pacman.cheat_mode:
            text += "\ncheat mode: on"
        self.draw_text_multiline(
            self.screen, text, 1000, 100, font=self.get_font(25)
        )
        pygame.display.update()

    def draw_to_menu(self, state: VisualState, dt: float):
        if state is None:
            print(f"returned early, {state}")
            return None
        target = self.surface_per_menu[state]
        if self.get_background(state) is not None:
            target.blit(self.get_background(state), (0, 0))
        else:
            target.fill((0, 0, 0))
        match state:
            case VisualState.IN_GAME:
                self.game_space.fill((0, 0, 0))
                self.draw_cells(self.game_space)
                if self.pacmap.pacman.cheat_mode:
                    self.draw_targets(self.game_space)
                self.draw_charachters(self.game_space)
                pos = (
                    Pos2D(
                        MainData.cell_size * self.CELL_MARGIN * 3,
                        MainData.cell_size * self.CELL_MARGIN * 3,
                    )
                    // 1
                )
                target.blit(self.game_space, pos)
            case VisualState.HIGH_SCORE_MENU:
                self.draw_text_multiline(
                    target,
                    "\n".join(
                        f'"{k}": {v}' for k, v in MainData.high_scores.items()
                    ),
                    200,
                    100,
                    font=self.get_font(25),
                )
            case VisualState.CONFIG:
                self.draw_text_multiline(
                    target,
                    "this is config",
                    200,
                    100,
                    font=self.get_font(25),
                )
            case VisualState.MAIN_MENU:
                pass

        mouse_pos = Pos2D(pygame.mouse.get_pos())
        for button in self.buttons_per_menu[state]:
            if isinstance(button, AnimatedButton):
                button.update(dt)
            target.blit(
                (
                    button.hovered_image
                    if button.is_in(mouse_pos)
                    else button.image
                ),
                button.to_screen_rect,
            )
            self.draw_text_multiline(
                target,
                button.text,
                button.to_screen_rect.x,
                button.to_screen_rect.y,
                font=button.font_size,
            )
        return target

    def event_handler(
        self, event: pygame.event.Event
    ) -> pygame.event.Event | int:
        """Handle a pygame event.
        dispatch to the appropriate handler based on event type and key.

        Args:
            event (pygame.event.Event): The event to handle.

        Returns:
            Optional[int]: The result of the event handling, if any.
        """
        if event.type == pygame.KEYDOWN:
            return self.keyboard_handler(event)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            event_pos = Pos2D(event.pos)
            for button in self.active_buttons:
                if button.is_in(event_pos):
                    button.on_click()
        elif event.type == pygame.VIDEORESIZE:
            # 1. Enforce Minimum Size
            min_size = (
                (
                    Pos2D(
                        MainData.config_from_file["width"],
                        MainData.config_from_file["height"],
                    )
                    + (Pos2D(self.CELL_MARGIN, self.CELL_MARGIN) * 2)
                )
                * MainData.cell_size
                * 3
            )
            min_size //= 1

            new_w = max(min_size.x, event.w)
            new_h = max(min_size.y, event.h)
            if (new_w, new_h) != event.size:
                self.screen = pygame.display.set_mode(
                    (new_w, new_h), pygame.RESIZABLE
                )
            for k, value in self.surface_per_menu.items():
                self.surface_per_menu[k] = pygame.surface.Surface(
                    (new_w, new_h)
                )
        return event

    def movement_scan(self) -> None:
        """Scan for key input that can be maintained."""
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            self.pacmap.pacman.next_direction = Direction.NORTH
        if keys[pygame.K_RIGHT]:
            self.pacmap.pacman.next_direction = Direction.EAST
        if keys[pygame.K_DOWN]:
            self.pacmap.pacman.next_direction = Direction.SOUTH
        if keys[pygame.K_LEFT]:
            self.pacmap.pacman.next_direction = Direction.WEST

    def draw_targets(self, target: pygame.surface.Surface) -> None:
        for ghost in self.pacmap.ghosts:
            if ghost.target_cell:
                start = ghost.target_cell * (MainData.cell_size)
                rect = (
                    start.x,
                    start.y,
                    MainData.cell_size,
                    MainData.cell_size,
                )
                target.fill(ghost.ghost_color, rect)

    def draw_charachters(self, target: pygame.surface.Surface) -> None:
        charachters: list[MovingEntities] = [
            self.pacmap.pacman
        ] + self.pacmap.ghosts
        self.Counter += 1
        for charachter in charachters:
            if self.Counter % 5 == 0:
                charachter.incr_anim()
            pos = (charachter.visual_pos) * MainData.cell_size
            target.blit(charachter.image, pos)

    def draw_cells(self, target: pygame.surface.Surface) -> None:
        for x, row in enumerate(self.pacmap.cells):
            for y, cell in enumerate(row):
                for x2 in range(3):
                    for y2 in range(3):
                        if (x + y + x2 + y2) & 1:
                            rect = pygame.Rect(
                                ((x * 3 + x2) * MainData.cell_size),
                                ((y * 3 + y2) * MainData.cell_size),
                                MainData.cell_size,
                                MainData.cell_size,
                            )
                            target.fill(pygame.Color(20, 20, 80), rect)
                        target.blit(
                            cell.image[x2][y2],
                            (
                                (x * 3 + x2) * MainData.cell_size,
                                (y * 3 + y2) * MainData.cell_size,
                            ),
                        )
                        if cell.fruit:
                            image = cell.fruit.image
                            target.blit(
                                image,
                                (
                                    (x * 3 + 1) * MainData.cell_size,
                                    (y * 3 + 1) * MainData.cell_size,
                                ),
                            )

    def get_font(self, size: Optional[int] = None) -> pygame.font.Font:
        """Get a font for rendering text.
        Caches fonts by size to avoid creating multiple font objects.
        If size is None, returns a font scaled to \
            the current camera zoom level.

        Args:
            size (Optional[int], optional): \
                The size of the font. Defaults to None.

        Returns:
            pygame.font.Font: The font object.
        """
        if size is None:
            size = max(1, self.base_font_size)

        if size not in self.font_cache:
            self.font_cache[size] = pygame.font.SysFont("monospace", size)

        return self.font_cache[size]

    def draw_text_multiline(
        self,
        target: pygame.surface.Surface,
        text: str,
        x: int,
        y: int,
        line_spacing: int = 2,
        color: tuple[int, int, int] = (255, 255, 255),
        font: Optional[pygame.font.Font] = None,
    ) -> None:
        """Draw text on the screen, allowing for multiline text.

        Args:
            text (str): The text to draw.
            x (int): The x position to \
                start drawing the text.
            y (int): The y position to \
                start drawing the text.
            line_spacing (int, optional): \
                The spacing between lines. Defaults to 2.
            color (tuple[int, int, int], optional): \
                The color of the text. Defaults to (255, 255, 255).
            font (Optional[pygame.font.Font], optional): \
                The font to use for the text. Defaults to None.
        """
        lines = text.split("\n")
        if font is None:
            font = self.get_font()
        for i, line in enumerate(lines):
            text_surface = font.render(line, True, color)
            target.blit(
                text_surface, (x, y + i * (font.get_height() + line_spacing))
            )

    def keyboard_handler(self, event: pygame.event):
        match event.key:
            case pygame.K_ESCAPE:
                return pygame.QUIT
            case pygame.K_n:
                self.autoplay = not self.autoplay
            case pygame.K_HOME:
                self.visualiser_state = VisualState.MAIN_MENU
            case pygame.K_RETURN:
                self.visualiser_state = VisualState.IN_GAME
            case pygame.K_r:
                self.pacmap.restart()
            case pygame.K_SPACE:
                self.pacmap.pacman.eat_wall()
            case pygame.K_t:
                self.pacmap.fright_time_left = self.pacmap.level[
                    "frightened_duration"
                ]
            case _:
                if self.verbose:
                    print(event)
        # konami sequence detection
        konami_code = [
            pygame.K_UP,
            pygame.K_UP,
            pygame.K_DOWN,
            pygame.K_DOWN,
            pygame.K_LEFT,
            pygame.K_RIGHT,
            pygame.K_LEFT,
            pygame.K_RIGHT,
            pygame.K_b,
            pygame.K_a,
        ]
        if event.key in [
            pygame.K_UP,
            pygame.K_RIGHT,
            pygame.K_DOWN,
            pygame.K_LEFT,
            pygame.K_b,
            pygame.K_a,
        ]:
            self.code_sequence.append(event.key)
            if self.code_sequence == [pygame.K_UP, pygame.K_UP, pygame.K_UP]:
                self.code_sequence.pop()
            elif self.code_sequence != konami_code[: len(self.code_sequence)]:
                self.code_sequence.clear()
            elif self.code_sequence == konami_code:
                self.pacmap.pacman.cheat_mode = (
                    not self.pacmap.pacman.cheat_mode
                )
                self.code_sequence.clear()

    def anim_transition(
        self,
        act: pygame.surface.Surface,
        prec: pygame.surface.Surface,
        dt: float,
    ):
        def zoom(image: pygame.surface.Surface, size: Pos2D):
            center = Pos2D(image.get_size()) / 2
            return image.subsurface(center - (size / 2), size)

        print(act, prec, self.act_anim)
        final_buf = self.surface_per_menu["final_buffer"]
        if self.act_anim:
            self.act_anim = max(
                0, self.act_anim - (dt * 1 / self.anim_duration)
            )
        if not self.act_anim:
            self.prec_state = None
            return act
        if self.act_anim:
            screen_size = Pos2D(self.screen.get_size())
            scaled_prec = pygame.transform.scale(prec, prec.get_size())
            match self.anim_type:
                case AnimTypes.LEFT_TO_RIGHT:
                    final_buf.blit(
                        scaled_prec,
                        (
                            scaled_prec.get_width()
                            - scaled_prec.get_width() * self.act_anim,
                            0,
                        ),
                    )
                    final_buf.blit(
                        act,
                        (
                            1 - act.get_width() * self.act_anim,
                            0,
                        ),
                    )
                case AnimTypes.RIGHT_TO_LEFT:
                    final_buf.blit(
                        scaled_prec,
                        (
                            scaled_prec.get_width()
                            + scaled_prec.get_width() * self.act_anim,
                            0,
                        ),
                    )
                    final_buf.blit(
                        act,
                        (
                            1 + act.get_width() * self.act_anim,
                            0,
                        ),
                    )
                case AnimTypes.UP_TO_DOWN:
                    final_buf.blit(
                        scaled_prec,
                        (
                            0,
                            scaled_prec.get_width()
                            - scaled_prec.get_width() * self.act_anim,
                        ),
                    )
                    final_buf.blit(
                        act,
                        (
                            0,
                            1 - (act.get_height() * self.act_anim),
                        ),
                    )
                case AnimTypes.DOWN_TO_UP:
                    final_buf.blit(
                        scaled_prec,
                        (
                            0,
                            scaled_prec.get_width()
                            - scaled_prec.get_width() * self.act_anim,
                        ),
                    )
                    final_buf.blit(
                        act,
                        (
                            0,
                            0 + (act.get_height() * self.act_anim),
                        ),
                    )

                case AnimTypes.ZOOM_IN:
                    center_part = pygame.transform.scale(
                        act, screen_size * (1 - self.act_anim)
                    )
                    extern_part = zoom(prec, screen_size * (self.act_anim**3))
                    extern_part = pygame.transform.scale(
                        extern_part, screen_size
                    )
                    final_buf.blit(extern_part, (0, 0))
                    # ...shrinking screen stays on top, disappearing into it
                    final_buf.blit(
                        center_part,
                        screen_size / 2 - (Pos2D(center_part.get_size()) / 2),
                    )

                case AnimTypes.ZOOM_OUT:
                    center_part = pygame.transform.scale(
                        prec, screen_size * (self.act_anim)
                    )
                    extern_part = zoom(act, screen_size * (1 - self.act_anim))
                    extern_part = pygame.transform.scale(
                        extern_part, screen_size
                    )
                    final_buf.blit(extern_part, (0, 0))
                    # ...shrinking screen stays on top, disappearing into it
                    final_buf.blit(
                        center_part,
                        screen_size / 2 - (Pos2D(center_part.get_size()) / 2),
                    )
        return final_buf

    def init_button(self):
        back_button = ClickableButton(
            0.9,
            0,
            0.1,
            0.1,
            self.screen,
            effect=DelayedCall(
                lambda vis: vis.change_state(
                    VisualState.MAIN_MENU,
                    vis.anim_duration,
                    vis.anim_type.oppo(),
                ),
                self,
            ),
            image=MainData.assets.get_asset("back.png", scaling=False),
        )
        in_game = [
            back_button,
            ClickableButton(
                0.4,
                0,
                0.2,
                0.05,
                self.screen,
                effect=DelayedCall(
                    lambda pac=self.pacmap: print(pac.score, pac.pacman.lives)
                ),
                text="get_score",
            ),
            ClickableButton(
                0.78,
                0,
                0.1,
                0.1,
                self.screen,
                effect=DelayedCall(
                    self.change_state, VisualState.IN_GAME_PAUSED
                ),
                image=MainData.assets.get_asset("unpaused.png", scaling=False),
            ),
        ]
        in_game_paused = [
            back_button,
            ClickableButton(
                0.78,
                0,
                0.1,
                0.1,
                self.screen,
                effect=DelayedCall(self.change_state, VisualState.IN_GAME),
                image=MainData.assets.get_asset("paused.png", scaling=False),
            ),
        ]

        paused_pacman = CyclicList(
            [
                MainData.assets.get_asset(
                    f"pacman_frame_{i}.png", size_multiplier=1.3
                )
                for i in range(4)
            ]
        )
        main_menu = [
            AnimatedButton(
                0.4,
                0.4,
                0.2,
                0.03,
                self.screen,
                DelayedCall(
                    self.change_state,
                    VisualState.IN_GAME,
                    anim_duration=1,
                    anim_type=AnimTypes.ZOOM_IN,
                ),
                text=DelayedCall(
                    lambda pacmap: (
                        "Start game"
                        if pacmap.total_elapsed_time == 0 or pacmap.is_finished
                        else "resume game"
                    ),
                    self.pacmap,
                ),
                animation_image=paused_pacman,
            ),
            AnimatedButton(
                0.4,
                0.45,
                0.2,
                0.03,
                self.screen,
                DelayedCall(
                    self.change_state,
                    VisualState.HIGH_SCORE_MENU,
                    1,
                    AnimTypes.LEFT_TO_RIGHT,
                ),
                text="High scores",
                animation_image=paused_pacman,
            ),
            AnimatedButton(
                0.4,
                0.50,
                0.2,
                0.03,
                self.screen,
                DelayedCall(self.change_state, VisualState.CONFIG),
                animation_image=paused_pacman,
            ),
        ]
        self.buttons_per_menu = {
            VisualState.IN_GAME: in_game,
            VisualState.IN_GAME_PAUSED: in_game_paused,
            VisualState.HIGH_SCORE_MENU: [back_button],
            VisualState.MAIN_MENU: main_menu,
            VisualState.CONFIG: [back_button],
        }
