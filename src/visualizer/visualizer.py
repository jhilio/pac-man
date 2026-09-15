from __future__ import annotations

from typing import Optional, cast
import pygame
from random import Random
from pygame.surface import Surface
from ..ai.interface import NNDirectionChooser
from ..cells import Cell
from ..charachters.moving_entity import MovingEntities
from ..config import MainData
from ..enums import AnimTypes, Direction, VisualState
from ..pacmap import PacMap, init_cells_from_2d
from ..vector import ColorRGB, Pos2D
from ..visualizer.button import (
    AnimatedButton,
    ClickableButton,
    CyclicList,
    DelayedCall,
    cheat_toggle_anim,
    pac_button_anim,
    pac_button_hover,
    paused_anim,
)
from .utils import draw_text_multiline


def random_list_bool(
    proportion: float, size: int = 100, seed: int = 42
) -> list[bool]:
    """return a list with a proportion
    of true/false that is shuffled with seed
    Args:
        proportion (float): what proportion of true
        size (int, optional: size of the list. Defaults to 100.
        seed (int, optional): the seed used to shufle. Defaults to 42.
    Returns:
        list[bool]: the shufled list
    """
    res = [i / proportion < size for i in range(size)]
    Random(seed).shuffle(res)
    return res


def zoom(image: Surface, size: Pos2D) -> Surface:
    """get a subsurface of the given size at center of image
    Args:
        image (Surface): source image
        size (Pos2D): size of the subsurface
    Returns:
        Surface: the zoomed subsurface
    """
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
        nn: Optional[NNDirectionChooser] = None,
    ):
        """initialise everything needed to visualise pacman

        Args:
            pacmap (PacMap): the map
            size (tuple[int, int], optional): size of the window.
                Defaults to (1000, 700).
            verbose (bool, optional):
                add aditional log message.
            Defaults to False.
            nn (Optional[NNDirectionChooser], optional):
                optional neural network contain in this interface.
                Defaults to None.
        """
        pygame.init()
        self.size = size
        self.fps = 60
        self.visualiser_state = VisualState.MAIN_MENU
        self.paused = False
        self.typed_name = ""
        self.autoplay = False
        self.pacmap = pacmap
        self.base_font_size = 13
        self.font_cache: dict[int, pygame.font.Font] = {}
        pygame.display.set_icon(
            MainData.assets.get_asset("pacman_frame_1.png")
        )
        self.screen = pygame.display.set_mode(size, pygame.RESIZABLE)
        pygame.display.set_caption("Pac-Man")
        self.code_sequence: list[int] = []
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
        }
        self.background_name_per_menu = {
            VisualState.CONFIG: "rightbg.png",
            VisualState.HIGH_SCORE_MENU: "leftbg.png",
            VisualState.MAIN_MENU: "BGmenu.jpg",
            VisualState.IN_GAME: "gameback.png",
            VisualState.PROMPTING_FOR_NAME: "gameback.png",
        }
        self.prec_state: Optional[VisualState] = None
        self.nn = nn
        self.anim_duration = 1.0
        self.anim_type = AnimTypes.LEFT_TO_RIGHT
        self.act_anim = 0.0
        self.custom_cell: list[list[Cell]] = init_cells_from_2d(
            [
                [9] + [1] * (len(self.pacmap.cells) - 2) + [3],
                [12] + [4] * (len(self.pacmap.cells) - 2) + [6],
            ],
            0,
            corner=False,
        )
        self.set_high_score_maze()

    def set_high_score_maze(self) -> None:
        self.high_maze: list[list[Cell]] = init_cells_from_2d(
            [
                [
                    9,
                    1,
                    1,
                    1,
                    1,
                    3,
                    9,
                    1,
                    1,
                    1,
                    1,
                    1,
                    1,
                    1,
                    1,
                    3,
                    9,
                    1,
                    1,
                    1,
                    1,
                    3,
                ],
                [
                    8,
                    0,
                    0,
                    0,
                    0,
                    2,
                    8,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    2,
                    8,
                    0,
                    0,
                    0,
                    0,
                    2,
                ],
                [
                    8,
                    0,
                    0,
                    0,
                    0,
                    2,
                    12,
                    4,
                    4,
                    4,
                    4,
                    4,
                    4,
                    4,
                    4,
                    6,
                    8,
                    0,
                    0,
                    0,
                    0,
                    2,
                ],
                [
                    12,
                    4,
                    4,
                    4,
                    4,
                    6,
                    15,
                    15,
                    15,
                    15,
                    15,
                    15,
                    15,
                    15,
                    15,
                    15,
                    8,
                    0,
                    0,
                    0,
                    0,
                    2,
                ],
                [
                    15,
                    15,
                    15,
                    15,
                    15,
                    15,
                    15,
                    15,
                    15,
                    15,
                    15,
                    15,
                    15,
                    15,
                    15,
                    15,
                    12,
                    4,
                    4,
                    4,
                    4,
                    6,
                ],
                [
                    13,
                    5,
                    5,
                    7,
                    13,
                    5,
                    5,
                    5,
                    5,
                    5,
                    5,
                    5,
                    5,
                    5,
                    5,
                    7,
                    9,
                    1,
                    1,
                    1,
                    1,
                    3,
                ],
                [
                    13,
                    5,
                    5,
                    7,
                    13,
                    5,
                    5,
                    5,
                    5,
                    5,
                    5,
                    5,
                    5,
                    5,
                    5,
                    7,
                    8,
                    0,
                    0,
                    0,
                    0,
                    2,
                ],
                [
                    13,
                    5,
                    5,
                    7,
                    13,
                    5,
                    5,
                    5,
                    5,
                    5,
                    5,
                    5,
                    5,
                    5,
                    5,
                    7,
                    8,
                    0,
                    0,
                    0,
                    0,
                    2,
                ],
                [
                    13,
                    5,
                    5,
                    7,
                    13,
                    5,
                    5,
                    5,
                    5,
                    5,
                    5,
                    5,
                    5,
                    5,
                    5,
                    7,
                    8,
                    0,
                    0,
                    0,
                    0,
                    2,
                ],
                [
                    13,
                    5,
                    5,
                    7,
                    13,
                    5,
                    5,
                    5,
                    5,
                    5,
                    5,
                    5,
                    5,
                    5,
                    5,
                    7,
                    8,
                    0,
                    0,
                    0,
                    0,
                    2,
                ],
                [
                    13,
                    5,
                    5,
                    7,
                    13,
                    5,
                    5,
                    5,
                    5,
                    5,
                    5,
                    5,
                    5,
                    5,
                    5,
                    7,
                    8,
                    0,
                    0,
                    0,
                    0,
                    2,
                ],
                [
                    13,
                    5,
                    5,
                    7,
                    13,
                    5,
                    5,
                    5,
                    5,
                    5,
                    5,
                    5,
                    5,
                    5,
                    5,
                    7,
                    12,
                    4,
                    4,
                    4,
                    4,
                    6,
                ],
            ],
            0,
            corner=False,
        )

    @property
    def active_buttons(self) -> list[AnimatedButton | ClickableButton]:
        """list buttons active in the current visual state

        Returns:
            list[AnimatedButton | ClickableButton]: all actives buttons
        """
        return self.buttons_per_menu.get(self.visualiser_state, [])

    def get_background(self, state: VisualState) -> Surface | None:
        """get the background corresponding to given state
        Args:
            state (VisualState): which background is asked
        Returns:
            Surface | None: the background found if there is one else None
        """
        bg_name = self.background_name_per_menu.get(state, None)
        if bg_name is None:
            return None
        bg = MainData.assets.get_asset(bg_name, self.screen.get_size())
        return bg

    def change_state(
        self,
        new: VisualState,
        anim_duration: float = 0,
        anim_type: AnimTypes = AnimTypes.LEFT_TO_RIGHT,
    ) -> None:
        """change the state of the visualiser and start
        the given animation if there is one given

        Args:
            new (VisualState): new VisualState to go to
            anim_duration (float, optional):
                how many seconds the anim will last. Defaults to 0.
            anim_type (AnimTypes, optional):
                what type of animation to use.
                Defaults to AnimTypes.LEFT_TO_RIGHT.
        """
        if anim_duration and self.visualiser_state != new:
            self.prec_state = self.visualiser_state
            self.anim_duration = max(anim_duration, 0.000001)
            self.act_anim = 1.0 - self.act_anim
            self.anim_type = anim_type
        self.visualiser_state = new

    def launch_loop(self) -> None:
        self.time: float = 0.0
        self.loop()

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
                    pygame.quit()
                    return
            self.movement_scan()
            self.time += dt
            if (
                self.visualiser_state == VisualState.IN_GAME
                and not self.act_anim
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
        """call drawing depending on the internal state

        Args:
            dt (float): time since last frame
        """
        if self.prec_state is not None:
            actual = self.draw_to_menu(
                self.visualiser_state,
                self.surface_per_menu[self.visualiser_state],
                dt,
            )
            prec = self.draw_to_menu(
                self.prec_state, self.surface_per_menu[self.prec_state], dt
            )
            self.anim_transition(actual, prec, dt)
        else:
            self.draw_to_menu(self.visualiser_state, self.screen, dt)
        pygame.display.update()

    def draw_to_menu(
        self, state: VisualState, target: Surface, dt: float
    ) -> Surface:
        """draw everything needed for the given state to the given surface
        Args:
            state (VisualState): what state/menu should be drawn
            target (Surface): where to draw
            dt (float): delta_time since last frame

        Returns:
            Surface: the given surface
        """
        background = self.get_background(state)
        if background is not None:
            target.blit(background, (0, 0))
        else:
            target.fill((0, 0, 0))
        if state in [VisualState.IN_GAME, VisualState.PROMPTING_FOR_NAME]:
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
            game_offset = Pos2D(target.get_size()) / 2 - game_size / 2
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
                + Pos2D(0, len(self.pacmap.cells[0]) * MainData.cell_size * 3),
                self.custom_cell,
            )
            if self.pacmap.pacman.cheat_mode:
                self.draw_targets(target, offset)
            self.draw_charachters(target, offset)
            self.draw_hud(target, offset)
            self.draw_timer(target, offset - Pos2D(MainData.cell_size, 0))
        elif state == VisualState.HIGH_SCORE_MENU:
            shortest_side = min(target.get_size())
            longest_maze = (
                max(len(self.high_maze), len(self.high_maze[0]))
                + (self.CELL_MARGIN * 2)
            ) * 3
            if shortest_side // longest_maze != MainData.cell_size:
                MainData.cell_size = int(shortest_side // longest_maze * 0.85)
                for col in self.high_maze:
                    for cell in col:
                        cell.init_image()
            game_size = (
                Pos2D(
                    MainData.cell_size * len(self.high_maze),
                    MainData.cell_size * len(self.high_maze[0]),
                )
                * 3
            )
            offset = Pos2D(target.get_size()) / 2 - game_size / 2
            self.draw_cells(target, offset, self.high_maze)
            self.draw_high_scores(target, offset)
        mouse_pos = Pos2D(pygame.mouse.get_pos())
        for button in self.buttons_per_menu[state]:
            button.update(dt, button.is_in(mouse_pos))
            target.blit(
                (button.image),
                button.to_screen_rect,
            )
        return target

    def event_handler(self, event: pygame.event.Event) -> pygame.event.Event:
        """Handle a pygame event.
        dispatch to the appropriate handler based on event type and key.
        Args:
            event (pygame.event.Event): The event to handle.
        Returns:
            pygame.event.Event:
                The given event or pygame.quit event if necessary
        """
        if (
            self.visualiser_state == VisualState.PROMPTING_FOR_NAME
            and event.type
            in [
                pygame.KEYDOWN,
                pygame.TEXTINPUT,
            ]
        ):
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE and self.typed_name:
                    self.typed_name = self.typed_name[:-1]
                elif event.key == pygame.K_RETURN and self.typed_name.strip():
                    self.finish_entering_name()
            elif (
                event.type == pygame.TEXTINPUT
                and len(self.typed_name) < 10
                and (event.text.isalnum() or event.text.isspace())
            ):
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
                self.surface_per_menu[k] = Surface((new_w, new_h))
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

    def draw_targets(self, target: Surface, offset: Pos2D) -> None:
        """draw each ghost target cell, mainly for debug purposes

        Args:
            target (Surface): surface to write to
            offset (Pos2D): offset to add to each pos writen to
        """
        for ghost in self.pacmap.ghosts:
            if ghost.target_cell:
                start = ghost.target_cell * (MainData.cell_size) + offset
                rect = (
                    start.x,
                    start.y,
                    MainData.cell_size,
                    MainData.cell_size,
                )
                target.fill(getattr(ghost, "ghost_color", (0, 0, 0)), rect)

    def draw_charachters(self, target: Surface, offset: Pos2D) -> None:
        """draw self.pacmap.pacman and each
        of self.pacmap.ghost to the given surface

        Args:
            target (Surface): surface to write to
            offset (Pos2D): offset to add to each pos writen to
        """
        charachters: list[MovingEntities] = [
            self.pacmap.pacman,
            *self.pacmap.ghosts,
        ]

        self.Counter += 1
        for charachter in charachters:
            if self.Counter % 5 == 0:
                charachter.incr_anim()
            pos = (charachter.visual_pos) * MainData.cell_size
            target.blit(charachter.image, pos + offset)

    def draw_cells(
        self,
        target: Surface,
        offset: Pos2D,
        cells: list[list[Cell]],
    ) -> None:
        """draw each cell of the given list

        Args:
          target (Surface): surface to write to
          offset (Pos2D): offset to add to each pos writen to
          cells (list[list[Cell]]): cells to write
        """
        for x, row in enumerate(cells):
            for y, cell in enumerate(row):
                target.blit(
                    cell.image,
                    offset
                    + (x * 3 * MainData.cell_size, y * 3 * MainData.cell_size),
                )

    def draw_timer(self, target: Surface, offset: Pos2D) -> None:
        """calculate the proportion of time passed and
        draw a smaller and smaller timer goind from
        green to yellow to red as time pass

        Args:
            target (Surface): surface to write to
            offset (Pos2D): offset to add to each pos writen to
        """
        ratio = 1 - (
            (self.pacmap.level["duration"] - self.pacmap.total_elapsed_time)
            / self.pacmap.level["duration"]
        )

        color = (
            ColorRGB(0, 255, 100)
            .lerp(ColorRGB(255, 220, 0), min(ratio * 2, 1))
            .lerp(ColorRGB(255, 20, 20), max(ratio * 2 - 1, 0))
        )
        y_start = ratio * (target.get_height() - (offset.y * 2))
        y_start = round(y_start)
        target.fill(
            cast(tuple[int, int, int], tuple(round(color, 0))),
            (
                0 + offset.x,
                y_start + offset.y,
                MainData.cell_size,
                target.get_height() - (offset.y * 2) - y_start,
            ),
        )

    def draw_hud(self, target: Surface, offset: Pos2D) -> None:
        """draw the cells beneath the maze and the text in it

        Args:
            target (Surface): surface to write to
            offset (Pos2D): offset to add to each pos writen to
        """

        def cell_to_screen(pos: Pos2D) -> tuple[int, int]:
            pos = pos * MainData.cell_size * 3 + offset
            return round(pos.x), round(pos.y)

        font = self.get_font(MainData.cell_size * 3)
        right_top = Pos2D(
            0.25,
            len(self.pacmap.cells[0]),
        )
        draw_text_multiline(
            target,
            [char for char in "Score"],
            *cell_to_screen(right_top),
            font,
            block_spacing=MainData.cell_size * 3,
        )
        draw_text_multiline(
            target,
            [char for char in f"{self.pacmap.score:05}"],
            *cell_to_screen(right_top + (0, 1)),
            font,
            block_spacing=MainData.cell_size * 3,
            color=(pygame.color.THECOLORS["yellow"]),
        )

        center = Pos2D(
            len(self.pacmap.cells) // 2,
            len(self.pacmap.cells[0]),
        ) + (0.25, 0)
        draw_text_multiline(
            target,
            [char for char in "lvl"],
            *cell_to_screen(center + (-1, 0)),
            font,
            block_spacing=MainData.cell_size * 3,
        )
        draw_text_multiline(
            target,
            [char for char in f"{self.pacmap.level_num:02}"],
            *cell_to_screen(center + (-1, 1)),
            font,
            block_spacing=MainData.cell_size * 3,
            color=(pygame.color.THECOLORS["yellow"]),
        )

        start_score = Pos2D(
            len(self.pacmap.cells) - 1 - 4,
            len(self.pacmap.cells[0]),
        ) + (0.25, 0)

        draw_text_multiline(
            target,
            [char for char in "lives"],
            *cell_to_screen(start_score),
            font,
            block_spacing=MainData.cell_size * 3,
        )
        if self.pacmap.pacman.lives <= 6:
            for x in range(self.pacmap.pacman.lives - 1):
                pos = Pos2D(
                    len(self.pacmap.cells) - 1 - x,
                    len(self.pacmap.cells[0]) + 1,
                ) + (0.25, 0.25)
                target.blit(self.pacmap.pacman.raw_image, cell_to_screen(pos))
        else:
            offset_x = 2
            pos = Pos2D(
                len(self.pacmap.cells) - 1 - offset_x,
                len(self.pacmap.cells[0]) + 1,
            ) + (0.25, 0.25)
            target.blit(self.pacmap.pacman.raw_image, cell_to_screen(pos))
            draw_text_multiline(
                target,
                ["X", str(self.pacmap.pacman.lives - 1)],
                *cell_to_screen(pos + (1, -0.25)),
                font,
                block_spacing=MainData.cell_size * 3,
            )

    def draw_high_scores(self, target: Surface, offset: Pos2D) -> None:
        """draw MainData.high_score to the target surface at the given offset

        Args:
            target (Surface): surface to draw in
            offset (Pos2D): offset to add to every draw
        """
        font = self.get_font(MainData.cell_size * 3)
        m_font = self.get_font(int(MainData.cell_size * 3.75))
        big_font = self.get_font(int(MainData.cell_size * 4.5))
        list_top = list(MainData.high_scores.items())
        for i in range(10 - len(list_top)):
            list_top.append(("", 0))
        for i, (name, score) in enumerate(list_top[3:10], 5):
            pos = offset + (Pos2D(0.25, i) * MainData.cell_size * 3)
            draw_text_multiline(
                target,
                [char for char in f"{i-1:02}: {name}"],
                int(pos.x),
                int(pos.y),
                font,
                block_spacing=MainData.cell_size * 3,
            )
            pos_score = pos + (Pos2D(16, 0) * MainData.cell_size * 3)
            draw_text_multiline(
                target,
                [char for char in format(score, "06")],
                int(pos_score.x),
                int(pos_score.y),
                font,
                block_spacing=MainData.cell_size * 3,
                color=pygame.color.THECOLORS["yellow"],
            )

        for x, y, index, font in [(0, 1.75, 1, m_font), (16, 3, 2, font)]:
            name = list_top[index][0]
            if len(name) > 6:
                name = name[:-5] + "-\n" + name[-5:]
            y -= name.count("\n")
            pos = offset + (Pos2D(x + 0.25, y) * MainData.cell_size * 3)
            draw_text_multiline(
                target,
                [char for char in name],
                int(pos.x),
                int(pos.y),
                font,
                block_spacing=MainData.cell_size * 3,
                line_spacing=(MainData.cell_size * 3),
            )
            score_pos = pos + (
                Pos2D(0, 1 + name.count("\n")) * MainData.cell_size * 3
            )
            draw_text_multiline(
                target,
                [char for char in f"{list_top[index][1]:06}"],
                int(score_pos.x),
                int(score_pos.y),
                font,
                block_spacing=MainData.cell_size * 3,
                line_spacing=(MainData.cell_size * 3),
                color=pygame.color.THECOLORS["yellow"],
            )
        pos = offset + (Pos2D(6, 0.25) * MainData.cell_size * 3)
        draw_text_multiline(
            target,
            [char for char in list_top[0][0]],
            int(pos.x),
            int(pos.y),
            big_font,
            block_spacing=MainData.cell_size * 3,
        )
        score_pos = pos + (Pos2D(0, 1.25) * MainData.cell_size * 3)
        draw_text_multiline(
            target,
            [char for char in f"{list_top[0][1]:010}"],
            int(score_pos.x),
            int(score_pos.y),
            big_font,
            block_spacing=MainData.cell_size * 3,
            color=pygame.color.THECOLORS["yellow"],
        )

    def get_font(self, size: Optional[int] = None) -> pygame.font.Font:
        """Get a font for rendering text.
        Caches fonts by size to avoid creating multiple font objects.
        If size is None, returns a font scaled to \
            self.base_font_size.

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

    def keyboard_handler(
        self, event: pygame.event.Event
    ) -> pygame.event.Event:
        """dispatch keyboard event

        Args:
            event (pygame.event.Event): a keydown event

        Returns:
            pygame.event.Event: the given event
        """
        match event.key:
            case pygame.K_n:
                self.autoplay = not self.autoplay
            case pygame.K_s:
                if (
                    self.pacmap.pacman.cheat_mode
                    and not self.pacmap.is_finished
                ):
                    for col in self.pacmap.cells:
                        for cell in col:
                            cell.fruit.eated()
            case pygame.K_RETURN:
                if (
                    AnimatedButton.last_hovered is not None
                    and AnimatedButton.last_hovered in self.active_buttons
                ):
                    AnimatedButton.last_hovered.on_click()
            case pygame.K_ESCAPE:
                self.back_button.on_click()
            case pygame.K_r:
                if self.pacmap.pacman.cheat_mode:
                    self.pacmap.restart()
            case pygame.K_SPACE:
                self.pacmap.pacman.eat_wall()
            case pygame.K_UP:
                last = AnimatedButton.last_hovered
                if (
                    self.visualiser_state == VisualState.MAIN_MENU
                    and isinstance(last, AnimatedButton)
                ):
                    buttons = self.active_buttons
                    chosen = buttons[(buttons.index(last) - 1) % len(buttons)]
                    if isinstance(chosen, AnimatedButton):
                        AnimatedButton.last_hovered = chosen
            case pygame.K_DOWN:
                last = AnimatedButton.last_hovered
                if (
                    self.visualiser_state == VisualState.MAIN_MENU
                    and isinstance(last, AnimatedButton)
                ):
                    buttons = self.active_buttons
                    chosen = buttons[(buttons.index(last) + 1) % len(buttons)]
                    if isinstance(chosen, AnimatedButton):
                        AnimatedButton.last_hovered = chosen
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
        if event.key in konami_code:
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
        act: Surface,
        prec: Surface,
        dt: float,
    ) -> Surface:
        """animate the two given surface
        on the screen scaling and placing
        them acordingly to self.anim_type and self.act_anim

        Args:
            act (Surface): new menu
            prec (Surface): precedent menu
            dt (float): how much time passed since last frame

        Returns:
            Surface: the screen being writen to
        """
        final_buf = self.screen
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
        elif self.anim_type in [
            AnimTypes.PIXEL_REPLACEMENT,
            AnimTypes.REV_PIXEL_REPLACEMENT,
        ]:
            final_buf.blit(prec, (0, 0))
            size = 50
            rev = self.anim_type == AnimTypes.REV_PIXEL_REPLACEMENT
            for i, boo in enumerate(
                random_list_bool(
                    self.act_anim if rev else (1 - self.act_anim), 2500
                )
            ):
                if boo != rev:
                    pos = Pos2D(i % size, i // size) * screen_size / size
                    rect = (*pos, screen_size.x / size, screen_size.y / size)
                    final_buf.blit(act, rect, rect)
        return final_buf

    def init_button(self) -> None:
        """initialise all buttons of the visualizer"""
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
        main_menu: list[ClickableButton | AnimatedButton] = [
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
                    anim_type=AnimTypes.PIXEL_REPLACEMENT,
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
                effect=DelayedCall(
                    self.change_state,
                    VisualState.CONFIG,
                    1,
                    AnimTypes.RIGHT_TO_LEFT,
                ),
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

        option_button = AnimatedButton(
            0.20,
            0.2,
            0.4,
            0.6,
            self.screen,
            self.get_font(25),
            self.pacmap.pacman,
            animation_image=CyclicList(
                [
                    MainData.assets.get_asset(
                        "control_base.png", scaling=False
                    ),
                    MainData.assets.get_asset(
                        "control_cheat.png", scaling=False
                    ),
                ]
            ),
            anim_duration=0,
            animate_func=cheat_toggle_anim,
        )

        if isinstance(main_menu[0], AnimatedButton):
            AnimatedButton.last_hovered = main_menu[0]
        self.buttons_per_menu: dict[
            VisualState, list[ClickableButton | AnimatedButton]
        ] = {
            VisualState.IN_GAME: in_game,
            VisualState.HIGH_SCORE_MENU: [back_button],
            VisualState.MAIN_MENU: main_menu,
            VisualState.CONFIG: [option_button, back_button],
            VisualState.PROMPTING_FOR_NAME: prompting_for_name,
        }

    def start_entering_name(self) -> None:
        """start recording input for player name"""
        self.change_state(VisualState.PROMPTING_FOR_NAME)
        pygame.key.start_text_input()

    def finish_entering_name(self) -> None:
        """register the player name and update high score"""
        pygame.key.stop_text_input()
        self.pacmap.player_name = self.typed_name.strip()
        self.pacmap.update_high_score()
        self.paused = True
        self.pacmap.restart()
        self.back_button.on_click()
