
import pygame


def draw_text_multiline(
        target: pygame.surface.Surface,
        text: str,
        x: int,
        y: int,
        font: pygame.font.Font,
        line_spacing: int = 2,
        color: tuple[int, int, int] = (255, 255, 255),
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
    for i, line in enumerate(lines):
        text_surface = font.render(line, True, color)
        target.blit(
            text_surface, (x, y + i * (font.get_height() + line_spacing))
        )