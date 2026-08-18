from __future__ import annotations
import pygame
from .pacmap import PacMap
from .cells import Cell, sprites
from typing import Optional
from .enums import Direction
from .vector import Pos2D




cell_size = 16

class Visualizer:
    Counter=0

    def __init__(
            self,
            pacmap: PacMap,
            size: tuple[int, int] = (1000, 700)
        ):
        pygame.init()
        self.size = size
        self.tick_rate = 7.5
        self.fps = 60
        self.paused = True
        self.pacmap = pacmap
        self.base_font_size = 13
        self.font_cache: dict[int, pygame.font.Font] = {}
        self.screen = pygame.display.set_mode(size)
        self.launch_loop()

    def launch_loop(self) -> None:
        self.time: float = 0.0
        self.sim_accumulator = 0.0
        self.loop()

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

    def loop(self) -> None:
        """Main loop of the visualizer."""
        clock = pygame.time.Clock()
        while True:
            dt = clock.tick(self.fps) / 1000.0 * self.tick_rate  # seconds since last frame
            for event in pygame.event.get():
                if self.event_handler(event) == pygame.QUIT:
                    pygame.quit()
                    return
            self.movement_scan()
            
            self.time += dt
            if not self.paused:
                self.pacmap.update(dt)
            self.draw_all()


    def draw_all(self):
        self.screen.fill(pygame.Color(0, 0, 0))
        self.draw_cells()
        self.draw_charachters()
        self.draw_text_multiline(f"Score: {self.pacmap.score}", 1000, 100, font=self.get_font(25))
        pygame.display.update()

    def draw_charachters(self):
        pac = self.pacmap.pacman
        pac_dir = pac.direction
        frame = pac.anim_frames[pac.anim_step]
        self.Counter += 1
        if self.Counter % 5 == 0:
            pac.anim_step = (pac.anim_step + 1) % (len(pac.anim_frames))
        pos = (pac.visual_pos) * cell_size
        self.screen.blit(pygame.transform.scale(pac_dir.rotate(frame), (cell_size*1.5, cell_size* 1.5)), pos)


        
    def draw_cells(self):
        for x, row in enumerate(self.pacmap.cells):
            for y, cell in enumerate(row):
                for x2 in range(3):
                    for y2 in range(3):
                        if (x + y + x2 +y2) & 1:
                            rect = (((x*3 + x2) * cell_size),
                                    ((y*3 + y2) * cell_size),
                                    cell_size,
                                    cell_size)
                            self.screen.fill(pygame.Color(20,20,80), rect)
                        self.screen.blit(cell.image[x2][y2], ((x*3 +x2) *cell_size , (y*3+y2)*cell_size))
                        if cell.fruit:
                            self.screen.blit(cell.fruit.image, ((x*3 +1) *cell_size , (y*3+1)*cell_size))

                        
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
            self.display_keybind = False
            self.paused = False
            match event.key:
                case pygame.K_ESCAPE:
                    return pygame.QUIT
                case pygame.K_r:
                    self.pacmap.regenerate()
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
