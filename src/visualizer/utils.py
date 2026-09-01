
from pygame.surface import Surface
from pygame.font import Font

type ColorValue = tuple[int, int, int] | tuple[int, int, int, int]


def draw_text_multiline(
    target: Surface,
    text: str | list[str],
    x: int,
    y: int,
    font: Font,
    line_spacing: int = 2,
    block_spacing: int = 2,
    color: ColorValue = (255, 255, 255),
) -> None:
    """draw text to given surface
    Args:
        target (Surface): on what to draw the text
        text (str | list[str]): the text to draw
        x (int): The x position to start drawing the text. \
        y (int): The y position to start drawing the text.\
        font (Font): the font to use
        line_spacing (int, optional):
            how much space between lines.
            Defaults to 2.
        block_spacing (int, optional):
            how much space between block of text (if using list of str).
            Defaults to 2.
        color (ColorValue, optional):
            color of text.
            Defaults to (255, 255, 255). (white)
    """
    if isinstance(text, list):
        for i, block in enumerate(text):
            draw_text_multiline(
                target,
                block,
                x + (i * block_spacing),
                y,
                font,
                line_spacing,
                block_spacing,
                color,
            )
        return
    lines = text.split("\n")
    for i, line in enumerate(lines):
        text_surface = font.render(line, True, color)
        target.blit(
            text_surface, (x, y + i * (font.get_height() + line_spacing))
        )
