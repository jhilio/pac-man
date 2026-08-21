from __future__ import annotations
import json
from token import OP
import pygame
from typing import Callable, Optional
from .vector import Pos2D
from .charachters.ghost import get_ghost_state
from .charachters.moving_entity import MovingEntities
from .pacmap import PacMap
from .enums import Direction, VisualState
from .config import MainData


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
        print("finished")


class ClickableButton:
    def __init__(self, start:Pos2D, end:Pos2D, effect:Optional[DelayedCall]=None, text:str="", font_size:Optional[int]=None):
        self.start = start
        self.end = end
        self.size = end - start
        self.effect = effect
        self.text = text
        self.font_size = font_size


    def is_in(self, pos:Pos2D):
        return (
            self.start.x <=pos.x <=self.end.x
            and self.start.y <=pos.y <=self.end.y
            )
            
    

    def on_click(self):
        if self.effect:
            self.effect()

    @property
    def image(self): 
        surface = pygame.Surface(self.size)
        surface.fill((80, 80, 80))
        return surface

    @property
    def hovered_image(self): 
        surface = pygame.Surface(self.size)
        surface.fill((150, 150, 150))
        return surface


class Visualizer:
    Counter=0

    def __init__(
            self,
            pacmap: PacMap,
            size: tuple[int, int] = (1000, 700),
            verbose=False
        ):
        pygame.init()
        self.size = size
        self.fps = 60
        self.visualiser_state = VisualState.MAIN_MENU 
        self.paused = False
        self.pacmap = pacmap
        self.base_font_size = 13
        self.font_cache: dict[int, pygame.font.Font] = {}
        self.screen = pygame.display.set_mode(size, pygame.RESIZABLE)
        self.code_sequence = []
        self.verbose = verbose
        self.buttons_per_menu = {
            VisualState.MAIN_MENU: [
                ClickableButton(Pos2D(10, 10), Pos2D(200, 40), DelayedCall(self.change_state, VisualState.IN_GAME))
            ],
        }
            

    @property
    def active_buttons(self):
        return self.buttons_per_menu.get(self.visualiser_state, [])

    def change_state(self, new:VisualState):
        self.visualiser_state = new


    def launch_loop(self) -> None:
        self.time: float = 0.0
        self.loop()


    def save_high_score(self):
        with open("high_scores.json", "w") as file:
            json.dump(MainData.high_scores,file, indent=2)


    def loop(self) -> None:
        """Main loop of the visualizer."""
        clock = pygame.time.Clock()
        while True:
            dt = clock.tick(self.fps) / 1000.0  # seconds since last frame
            for event in pygame.event.get():
                if self.event_handler(event) == pygame.QUIT:
                    self.pacmap.update_high_score()
                    self.save_high_score()
                    pygame.quit()
                    return
            #MainData.cell_size = min(pygame.display.get_window_size()) // (min(len(self.pacmap.cells), len(self.pacmap.cells[0])) + 50)
            self.time += dt
            if self.visualiser_state == VisualState.IN_GAME:
                self.movement_scan()
                self.pacmap.update(dt)
                if not self.pacmap.pacman.lives >=1:
                    self.visualiser_state = VisualState.PROMPTING_FOR_NAME
            self.draw_dispatcher(dt)


    def draw_dispatcher(self, dt:float):
        self.screen.fill(pygame.Color(0, 0, 0))
        text =f"""
        {("fright left : " + format(self.pacmap.fright_time_left, ".1f") + "s") if self.pacmap.fright_time_left else ""}
        Time left : {self.pacmap.level["duration"] - self.pacmap.total_elapsed_time:.0f}S
        Phase state : {get_ghost_state().name} {self.pacmap.phase_timer}S
        Score: {self.pacmap.score}
        Current Level: {self.pacmap.level_num}
        lives : {self.pacmap.pacman.lives}
        cell_size : {MainData.cell_size}
        fps : {1/dt:.1f}
        """

        menu_text = "pless enter to play"
        match self.visualiser_state:
            case VisualState.MAIN_MENU:
                self.draw_text_multiline(menu_text, 200, 100, font=self.get_font(25))
            case VisualState.IN_GAME | VisualState.IN_GAME_PAUSED | VisualState.PROMPTING_FOR_NAME:
                self.draw_cells()
                if self.pacmap.pacman.cheat_mode:
                    self.draw_targets()
                self.draw_charachters()
                if self.visualiser_state is VisualState.IN_GAME_PAUSED:
                    self.draw_text_multiline("PAUSED", 200, 100, font=self.get_font(25))
                    pass # display the paused menu
                if self.visualiser_state is VisualState.PROMPTING_FOR_NAME:
                    pass # ask for player name
                    #self.pacmap.player_name = the_name
                    self.draw_text_multiline("name ?", 200, 100, font=self.get_font(25))
                    self.pacmap.update_high_score()
            case VisualState.HIGH_SCORE_MENU:
                self.draw_text_multiline("\n".join(f'"{k}": {v}' for k, v in MainData.high_scores.items()), 200, 100, font=self.get_font(25))

        mouse_pos = Pos2D(pygame.mouse.get_pos())
        for button in self.active_buttons:
            self.screen.blit(button.hovered_image if button.is_in(mouse_pos) else button.image, button.start)
            self.draw_text_multiline(button.text, button.start.x, button.start.y, font=button.font_size)
        if self.pacmap.pacman.cheat_mode:
            text += "\ncheat mode: on"
        self.draw_text_multiline(text, 1000, 100, font=self.get_font(25))
        pygame.display.update()


    def event_handler(self,
                      event: pygame.event.Event) -> pygame.event.Event | int:
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
            min_size = Pos2D(MainData.config_from_file["width"],MainData.config_from_file["height"]) * MainData.cell_size  * 3.3
            min_size //= 1

            new_w = max(min_size.x, event.w)
            new_h = max(min_size.y, event.h)
            if (new_w, new_h) != event.size:
                self.screen = pygame.display.set_mode((new_w, new_h), pygame.RESIZABLE)
        
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


    def draw_targets(self):
        for ghost in self.pacmap.ghosts:
            if ghost.target_cell:
                start = ghost.target_cell * (MainData.cell_size)
                rect =  (start.x, start.y, MainData.cell_size, MainData.cell_size)
                self.screen.fill(ghost.ghost_color, rect)

    def draw_charachters(self):
        charachters: list[MovingEntities] = [self.pacmap.pacman] + self.pacmap.ghosts
        self.Counter += 1
        for charachter in charachters:
            if self.Counter % 5 == 0:
                charachter.incr_anim()
            pos = (charachter.visual_pos) * MainData.cell_size
            self.screen.blit(charachter.image, pos)

    def draw_cells(self):
        for x, row in enumerate(self.pacmap.cells):
            for y, cell in enumerate(row):
                for x2 in range(3):
                    for y2 in range(3):
                        if (x + y + x2 +y2) & 1:
                            rect = pygame.Rect(((x*3 + x2) * MainData.cell_size),
                                    ((y*3 + y2) * MainData.cell_size),
                                    MainData.cell_size,
                                    MainData.cell_size)
                            self.screen.fill(pygame.Color(20,20,80), rect)
                        self.screen.blit(cell.image[x2][y2], ((x*3 +x2) *MainData.cell_size , (y*3+y2)*MainData.cell_size))
                        if cell.fruit:
                            image = cell.fruit.image
                            self.screen.blit(image, ((x*3 +1) *MainData.cell_size , (y*3+1)*MainData.cell_size))

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
            self.screen.blit(
                text_surface, (x, y + i * (font.get_height() + line_spacing))
            )


    def keyboard_handler(self, event:pygame.event):
        match event.key:
            case pygame.K_ESCAPE:
                return pygame.QUIT
            case pygame.K_BACKSPACE:
                if self.visualiser_state == VisualState.IN_GAME:
                    self.visualiser_state = VisualState.IN_GAME_PAUSED
                elif self.visualiser_state == VisualState.IN_GAME_PAUSED:
                    self.visualiser_state = VisualState.IN_GAME
            case pygame.K_s:
                if self.visualiser_state == VisualState.MAIN_MENU:
                    self.visualiser_state = VisualState.HIGH_SCORE_MENU
                elif self.visualiser_state == VisualState.HIGH_SCORE_MENU:
                    self.visualiser_state = VisualState.MAIN_MENU
            case pygame.K_HOME:
                self.visualiser_state = VisualState.MAIN_MENU
            case pygame.K_RETURN:
                self.visualiser_state = VisualState.IN_GAME
            case pygame.K_r:
                self.pacmap.regenerate()
            case pygame.K_SPACE:
                self.pacmap.pacman.eat_wall()
            case pygame.K_t:
                self.pacmap.fright_time_left = self.pacmap.level["frightened_duration"]
            case _:
                if self.verbose:
                    print(event)
        #konami sequence detection
        konami_code = [pygame.K_UP, pygame.K_UP, pygame.K_DOWN, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT, pygame.K_LEFT, pygame.K_RIGHT, pygame.K_b, pygame.K_a]
        if event.key in [pygame.K_UP, pygame.K_RIGHT, pygame.K_DOWN, pygame.K_LEFT, pygame.K_b, pygame.K_a]:
            self.code_sequence.append(event.key)
            if self.code_sequence == [pygame.K_UP, pygame.K_UP, pygame.K_UP]:
                self.code_sequence.pop()
            elif self.code_sequence !=konami_code[:len(self.code_sequence)]:
                self.code_sequence.clear()
            elif self.code_sequence == konami_code:
                self.pacmap.pacman.cheat_mode = not self.pacmap.pacman.cheat_mode
                self.code_sequence.clear()