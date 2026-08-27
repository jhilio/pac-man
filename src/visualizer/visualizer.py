from __future__ import annotations
import json
import pygame
from typing import Optional

from ..cells import Cell

from ..ai.interface import NNDirectionChooser
from ..vector import Pos2D, Rectangle, ColorRGB, Point
from ..charachters.ghost import get_ghost_state
from ..charachters.moving_entity import MovingEntities
from ..pacmap import PacMap
from ..enums import Direction, VisualState, AnimTypes
from ..config import MainData
from .utils import draw_text_multiline
from ..visualizer.button import (
    ClickableButton,
    DelayedCall,
    AnimatedButton,
    CyclicList,
    PercentRect,
    pac_button_anim,
    pac_button_hover,
    paused_anim,
)


def zoom(image: pygame.surface.Surface, size: Pos2D):
    center = Pos2D(image.get_size()) / 2
    return image.subsurface(center - (size / 2), size)


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
        self.paused = True
        self.typed_name = ""
        self.autoplay = False
        self.pacmap = pacmap
        self.base_font_size = 13
        self.font_cache: dict[int, pygame.font.Font] = {}
        self.screen = pygame.display.set_mode(size, pygame.RESIZABLE)
        self.code_sequence = []
        self.verbose = verbose
        game_size = (
            (
                Pos2D(
                    MainData.config_from_file["width"],
                    MainData.config_from_file["height"],
                )
                + Pos2D(self.CELL_MARGIN, self.CELL_MARGIN) * 2
            )
            * MainData.cell_size
            * 3
        ) // 1
        self.game_space = pygame.Surface(game_size)
        self.game_space.set_colorkey((0, 0, 0))
        self.init_button()
        game_copy = self.screen.copy()
        self.surface_per_menu = {
            VisualState.MAIN_MENU: self.screen.copy(),
            VisualState.CONFIG: self.screen.copy(),
            VisualState.HIGH_SCORE_MENU: self.screen.copy(),
            VisualState.IN_GAME: game_copy,
            VisualState.PROMPTING_FOR_NAME: game_copy,
            "final_buffer": self.screen.copy(),
        }
        self.background_name_per_menu = {
            VisualState.CONFIG: "BGmenu.jpg",
            VisualState.HIGH_SCORE_MENU: "leftbg.png",
            VisualState.MAIN_MENU: "BGmenu.jpg",
            VisualState.IN_GAME: "gameback.jpg",
            VisualState.PROMPTING_FOR_NAME: "gameback.jpg",
        }
        self.prec_state = None
        self.nn = nn
        self.anim_duration = 1
        self.anim_type = AnimTypes.LEFT_TO_RIGHT
        self.act_anim = 0
        y = len(self.pacmap.cells[0])
        custom_cell = []
        custom_cell.append(
            [Cell(9, 0, y, custom_cell), Cell(12, 0, y + 1, custom_cell)]
        )
        custom_cell.extend(
            [
                [Cell(1, x, y, custom_cell), Cell(4, x, y + 1, custom_cell)]
                for x in range(1, MainData.config_from_file["width"] - 1)
            ]
        )
        custom_cell.append(
            [
                Cell(
                    3, MainData.config_from_file["width"] - 1, y, custom_cell
                ),
                Cell(
                    6,
                    MainData.config_from_file["width"] - 1,
                    y + 1,
                    custom_cell,
                ),
            ]
        )
        self.custom_cell = custom_cell

    @property
    def active_buttons(self):
        return self.buttons_per_menu.get(self.visualiser_state, [])

    def get_background(self, state: VisualState):
        bg_name = self.background_name_per_menu.get(state, None)
        if bg_name is None:
            return None
        bg = MainData.assets.get_asset(bg_name, self.screen.get_size())
        return bg

    def change_state(
        self,
        new: VisualState,
        anim_duration=0,
        anim_type=AnimTypes.LEFT_TO_RIGHT,
    ):
        if anim_duration:
            self.prec_state = self.visualiser_state
            self.anim_duration = max(anim_duration, 0.000001)
            self.act_anim = 1 - self.act_anim
            self.anim_type = anim_type
        self.visualiser_state = new

    def launch_loop(self) -> None:

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
                if self.event_handler(event).type == pygame.QUIT:
                    self.pacmap.update_high_score()
                    self.save_high_score()
                    pygame.quit()
                    return
            # MainData.cell_size = min(pygame.display.get_window_size()) //
            # (min(len(self.pacmap.cells), len(self.pacmap.cells[0])) + 50)
            self.movement_scan()
            self.time += dt
            if (
                self.visualiser_state == VisualState.IN_GAME
                and not self.paused
                and not self.pacmap.is_finished
            ):
                if not self.autoplay or self.nn is None:
                    self.movement_scan()
                elif self.nn is not None and pacman.pos != prec_pos:
                    self.pacmap.pacman.next_direction = self.nn.choose(
                        self.pacmap
                    )
                prec_pos = pacman.pos
                self.pacmap.update(dt)
                if self.pacmap.is_finished:
                    if self.pacmap.player_name == "":
                        self.start_entering_name()
                    else:
                        self.pacmap.update_high_score()
                        self.paused = True
                        self.pacmap.restart()
                        self.back_button.on_click()
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

        if self.prec_state:
            finish_result = self.anim_transition(actual, prec, dt)
            self.screen.blit(finish_result, (0, 0))
        if self.pacmap.pacman.cheat_mode:
            text += "\ncheat mode: on"
        draw_text_multiline(
            self.screen, text, 1000, 100, font=self.get_font(25)
        )
        pygame.display.update()

    def draw_to_menu(self, state: VisualState, dt: float):
        if state is None:
            return None
        if self.prec_state:
            target = self.surface_per_menu[state]
        else:
            target = self.screen
        if self.get_background(state) is not None:
            target.blit(self.get_background(state), (0, 0))
        else:
            target.fill((0, 0, 0))
        match state:
            case VisualState.IN_GAME | VisualState.PROMPTING_FOR_NAME:
                shortest_side = min(target.get_size())
                longest_maze = (
                    max(len(self.pacmap.cells), len(self.pacmap.cells[0]))
                    + (self.CELL_MARGIN * 2)
                ) * 3
                if shortest_side // longest_maze != MainData.cell_size:
                    MainData.cell_size = shortest_side // longest_maze
                    for col in self.pacmap.cells + self.custom_cell:
                        for cell in col:
                            cell.init_image()
                game_size = Pos2D(
                    MainData.cell_size * longest_maze,
                    MainData.cell_size * longest_maze,
                )
                game_offset = (
                    Pos2D(target.get_size()) / 2 - Pos2D(game_size) / 2
                )
                offset = (
                    Pos2D(
                        MainData.cell_size * self.CELL_MARGIN * 3,
                        MainData.cell_size * self.CELL_MARGIN * 3,
                    )
                    // 1
                ) + game_offset
                self.draw_cells(target, offset, self.pacmap.cells)
                self.draw_cells(
                    target,
                    offset
                    + Pos2D(
                        0, len(self.pacmap.cells[0]) * MainData.cell_size * 3
                    ),
                    self.custom_cell,
                )
                if self.pacmap.pacman.cheat_mode:
                    self.draw_targets(target, offset)
                self.draw_charachters(target, offset)
                self.draw_timer(target, offset - Pos2D(MainData.cell_size, 0))
            case VisualState.CONFIG:
                draw_text_multiline(
                    target,
                    "shortcut:\narrow keys: movement\nr-> reload map\n"
                    + "n: togle neural network\nbackspace/delete: go back"
                    + "\nhome: return to main menu\n\nEnjoy !!",
                    500,
                    600,
                    font=self.get_font(35),
                )
            case VisualState.MAIN_MENU:
                pass

        mouse_pos = Pos2D(pygame.mouse.get_pos())
        if state == self.visualiser_state:
            for button in self.buttons_per_menu[state]:
                button.update(dt, button.is_in(mouse_pos))
                target.blit(
                    (button.image),
                    button.to_screen_rect,
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
        if (
            self.visualiser_state == VisualState.PROMPTING_FOR_NAME
            and event.type in [pygame.KEYDOWN, pygame.TEXTINPUT]
        ):
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE and self.typed_name:
                    self.typed_name = self.typed_name[:-1]
                elif event.key == pygame.K_RETURN and self.typed_name:
                    self.finish_entering_name()
            elif event.type == pygame.TEXTINPUT and len(self.typed_name) < 30:
                self.typed_name += event.text
        elif event.type == pygame.KEYDOWN:
            return self.keyboard_handler(event)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            event_pos = Pos2D(event.pos)
            for button in self.active_buttons:
                if button.is_in(event_pos):
                    button.on_click()
        elif event.type == pygame.VIDEORESIZE:
            # 1. Enforce Minimum Size
            min_size = Pos2D(self.game_space.get_size())

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
        a = True
        if keys[pygame.K_UP]:
            self.pacmap.pacman.next_direction = Direction.NORTH
        elif keys[pygame.K_RIGHT]:
            self.pacmap.pacman.next_direction = Direction.EAST
        elif keys[pygame.K_DOWN]:
            self.pacmap.pacman.next_direction = Direction.SOUTH
        elif keys[pygame.K_LEFT]:
            self.pacmap.pacman.next_direction = Direction.WEST
        else:
            a = False
        if a:
            self.paused = False

    def draw_targets(
        self, target: pygame.surface.Surface, offset: Pos2D
    ) -> None:
        for ghost in self.pacmap.ghosts:
            if ghost.target_cell:
                start = ghost.target_cell * (MainData.cell_size) + offset
                rect = (
                    start.x,
                    start.y,
                    MainData.cell_size,
                    MainData.cell_size,
                )
                target.fill(ghost.ghost_color, rect)

    def draw_charachters(
        self, target: pygame.surface.Surface, offset: Pos2D
    ) -> None:
        charachters: list[MovingEntities] = [
            self.pacmap.pacman
        ] + self.pacmap.ghosts
        self.Counter += 1
        for charachter in charachters:
            if self.Counter % 5 == 0:
                charachter.incr_anim()
            pos = (charachter.visual_pos) * MainData.cell_size
            target.blit(charachter.image, pos + offset)
        for x in range(self.pacmap.pacman.lives - 1):
            pos = (
                Pos2D(
                    len(self.pacmap.cells) - 1 - x, len(self.pacmap.cells[0])
                )
                * 3
                + (1, 1)
            ) * MainData.cell_size
            target.blit(self.pacmap.pacman.raw_image, pos + offset)

    def draw_cells(
        self,
        target: pygame.surface.Surface,
        offset: Pos2D,
        cells: list[list[Cell]],
    ) -> None:
        for x, row in enumerate(cells):
            for y, cell in enumerate(row):
                target.blit(
                    cell.image,
                    offset
                    + (x * 3 * MainData.cell_size, y * 3 * MainData.cell_size),
                )

    def draw_timer(self, target: pygame.surface.Surface, offset: Pos2D):
        ratio = (
            self.pacmap.level["duration"] - self.pacmap.total_elapsed_time
        ) / self.pacmap.level["duration"]
        color = ColorRGB(255, 80, 80).lerp(ColorRGB(80, 255, 80), ratio)
        target.fill(
            round(color, 0),
            (
                0 + offset.x,
                (1 - ratio) * target.get_height() + offset.y,
                MainData.cell_size,
                target.get_height()
                - (MainData.cell_size * self.CELL_MARGIN * 3 * 2),
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

    def keyboard_handler(self, event: pygame.event):
        match event.key:
            case pygame.K_ESCAPE:
                return pygame.event.Event(pygame.QUIT)
            case pygame.K_n:
                self.autoplay = not self.autoplay
            case pygame.K_HOME:
                self.visualiser_state = VisualState.MAIN_MENU
            case pygame.K_RETURN:
                if (
                    AnimatedButton.last_hovered is not None
                    and AnimatedButton.last_hovered in self.active_buttons
                ):
                    AnimatedButton.last_hovered.on_click()
            case pygame.K_BACKSPACE:
                self.back_button.on_click()
            case pygame.K_k:
                self.pacmap.pacman_died()
            case pygame.K_r:
                self.pacmap.restart()
            case pygame.K_SPACE:
                self.pacmap.pacman.eat_wall()
            case pygame.K_t:
                self.pacmap.fright_time_left = self.pacmap.level[
                    "frightened_duration"
                ]
            case pygame.K_UP:
                if self.visualiser_state == VisualState.MAIN_MENU:
                    AnimatedButton.last_hovered = self.active_buttons[
                        (
                            self.active_buttons.index(
                                AnimatedButton.last_hovered
                            )
                            - 1
                        )
                        % len(self.active_buttons)
                    ]
            case pygame.K_DOWN:
                if self.visualiser_state == VisualState.MAIN_MENU:
                    AnimatedButton.last_hovered = self.active_buttons[
                        (
                            self.active_buttons.index(
                                AnimatedButton.last_hovered
                            )
                            + 1
                        )
                        % len(self.active_buttons)
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
        return event

    def anim_transition(
        self,
        act: pygame.surface.Surface,
        prec: pygame.surface.Surface,
        dt: float,
    ):
        final_buf = self.surface_per_menu["final_buffer"]
        if self.act_anim:
            self.act_anim = max(
                0, self.act_anim - (dt * 1 / self.anim_duration)
            )
        if not self.act_anim:
            self.prec_state = None
            return act
        MIN_CENTER = 0.02
        screen_size = Pos2D(self.screen.get_size())
        scaled_prec = pygame.transform.scale(prec, prec.get_size())
        if self.anim_type in [
            AnimTypes.LEFT_TO_RIGHT,
            AnimTypes.RIGHT_TO_LEFT,
            AnimTypes.UP_TO_DOWN,
            AnimTypes.DOWN_TO_UP,
        ]:
            directions = {
                AnimTypes.LEFT_TO_RIGHT: (-1, 0),
                AnimTypes.RIGHT_TO_LEFT: (1, 0),
                AnimTypes.UP_TO_DOWN: (0, -1),
                AnimTypes.DOWN_TO_UP: (0, 1),
            }
            dx, dy = directions[self.anim_type]
            final_buf.blit(
                scaled_prec,
                (
                    dx * act.get_width() * (1 - self.act_anim) * -1,
                    dy * act.get_height() * (1 - self.act_anim) * -1,
                ),
            )
            final_buf.blit(
                act,
                (
                    dx * scaled_prec.get_width() * self.act_anim,
                    dy * scaled_prec.get_height() * self.act_anim,
                ),
            )
        elif self.anim_type == AnimTypes.ZOOM_IN:
            t = 1 - self.act_anim

            f = t * t * (3 - 2 * t)  # smoothstep
            center_scale = MIN_CENTER + (1.0 - MIN_CENTER) * f
            extern_scale = 1.0 - f
            center_part = pygame.transform.scale(
                act, screen_size * center_scale
            )
            extern_part = zoom(prec, screen_size * extern_scale)
            extern_part = pygame.transform.scale(extern_part, screen_size)
            final_buf.blit(extern_part, (0, 0))
            final_buf.blit(
                center_part,
                screen_size / 2 - (Pos2D(center_part.get_size()) / 2),
            )
        elif self.anim_type == AnimTypes.ZOOM_OUT:
            t = self.act_anim

            f = t * t * (3 - 2 * t)  # smoothstep
            center_scale = MIN_CENTER + (1.0 - MIN_CENTER) * f
            extern_scale = 1.0 - f
            center_part = pygame.transform.scale(
                prec, screen_size * center_scale
            )
            extern_part = zoom(act, screen_size * extern_scale)
            extern_part = pygame.transform.scale(extern_part, screen_size)
            final_buf.blit(extern_part, (0, 0))
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
            self.get_font(25),
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
        self.back_button = back_button
        in_game = [
            back_button,
            AnimatedButton(
                0.78,
                0,
                0.1,
                0.1,
                self.screen,
                self.get_font(25),
                self,
                effect=DelayedCall(
                    lambda self: setattr(self, "paused", not self.paused), self
                ),
                animation_image=CyclicList(
                    [
                        MainData.assets.get_asset(
                            "unpaused.png", scaling=False
                        ),
                        MainData.assets.get_asset("paused.png", scaling=False),
                    ]
                ),
                anim_duration=0,
                animate_func=paused_anim,
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
                0.35,
                0.4,
                0.3,
                0.05,
                self.screen,
                self.get_font(30),
                effect=DelayedCall(
                    self.change_state,
                    VisualState.IN_GAME,
                    anim_duration=1,
                    anim_type=AnimTypes.ZOOM_IN,
                ),
                text=DelayedCall(
                    lambda pacmap: (
                        "Start game"
                        if not pacmap.has_started
                        else "resume game"
                    ),
                    self.pacmap,
                ),
                image=MainData.assets.get_asset("button.png", scaling=False),
                animation_image=paused_pacman,
                animate_func=pac_button_anim,
                on_hover=pac_button_hover,
                animation_frames_count=10,
            ),
            AnimatedButton(
                0.35,
                0.475,
                0.3,
                0.05,
                self.screen,
                self.get_font(30),
                effect=DelayedCall(
                    lambda: self.change_state(
                        VisualState.HIGH_SCORE_MENU,
                        1,
                        AnimTypes.LEFT_TO_RIGHT,
                    )
                ),
                image=MainData.assets.get_asset("button.png", scaling=False),
                text="High scores",
                animation_image=paused_pacman,
                animate_func=pac_button_anim,
                on_hover=pac_button_hover,
                animation_frames_count=10,
            ),
            AnimatedButton(
                0.35,
                0.55,
                0.3,
                0.05,
                self.screen,
                self.get_font(30),
                effect=DelayedCall(self.change_state, VisualState.CONFIG),
                image=MainData.assets.get_asset("button.png", scaling=False),
                text="Controls",
                animation_image=paused_pacman,
                animate_func=pac_button_anim,
                on_hover=pac_button_hover,
                animation_frames_count=10,
            ),
            AnimatedButton(
                0.35,
                0.625,
                0.3,
                0.05,
                self.screen,
                self.get_font(30),
                effect=DelayedCall(
                    lambda: pygame.event.post(pygame.event.Event(pygame.QUIT))
                ),
                image=MainData.assets.get_asset("button.png", scaling=False),
                text="Quit",
                animation_image=paused_pacman,
                animate_func=pac_button_anim,
                on_hover=pac_button_hover,
                animation_frames_count=10,
            ),
        ]
        high_score = AnimatedButton(
            0.2,
            0.2,
            0.5,
            0.5,
            self.screen,
            self.get_font(25),
            image=MainData.assets.get_asset("control.png", scaling=False),
            text=DelayedCall(lambda data=MainData: "\n".join(
                    f'"{k}": {v}' for k, v in data.high_scores.items()
                )
            ),
        )
        prompting_for_name = [
            ClickableButton(
                0.35,
                0.3,
                0.3,
                0.1,
                self.screen,
                self.get_font(20),
                text=DelayedCall(
                    lambda vis: (
                        vis.typed_name if vis.typed_name else "type your name"
                    ),
                    self,
                ),
                image=MainData.assets.get_asset("button.png", scaling=False),
            )
        ]
        AnimatedButton.last_hovered = main_menu[0]
        self.buttons_per_menu: dict[VisualState, list[ClickableButton]] = {
            VisualState.IN_GAME: in_game,
            VisualState.HIGH_SCORE_MENU: [back_button, high_score],
            VisualState.MAIN_MENU: main_menu,
            VisualState.CONFIG: [back_button],
            VisualState.PROMPTING_FOR_NAME: prompting_for_name,
        }

    def start_entering_name(self):
        self.change_state(VisualState.PROMPTING_FOR_NAME)
        pygame.key.start_text_input()

    def finish_entering_name(self):
        pygame.key.stop_text_input()
        self.pacmap.player_name = self.typed_name
        self.pacmap.update_high_score()
        self.paused = True
        self.pacmap.restart()
        self.back_button.on_click()
