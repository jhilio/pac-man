from src.visualizer.visualizer import *


def draw_hud(self, target: pygame.surface.Surface, offset: Pos2D):
    font = self.get_font(MainData.cell_size * 3)
    start_score = (
        Pos2D(
            len(self.pacmap.cells) - 1 - 4,
            len(self.pacmap.cells[0]),
        )
        * MainData.cell_size
        * 3
    ) + offset
    draw_text_multiline(
        target,
        [char for char in "lives"],
        *start_score,
        font,
        block_spacing=MainData.cell_size * 3,
    )
    if self.pacmap.pacman.lives <= 6:
        for x in range(self.pacmap.pacman.lives - 1):
            pos = (
                Pos2D(
                    len(self.pacmap.cells) - 1 - x,
                    len(self.pacmap.cells[0]) + 1,
                )
                * 3
                + (0.75, 0.75)
            ) * MainData.cell_size
            target.blit(self.pacmap.pacman.raw_image, pos + offset)
    else:
        offset_x = 2
        pos = (
            Pos2D(
                len(self.pacmap.cells) - 1 - offset_x,
                len(self.pacmap.cells[0]) + 1,
            )
            * 3
            + (0.75, 0.75)
        ) * MainData.cell_size + offset
        target.blit(self.pacmap.pacman.raw_image, pos)
        draw_text_multiline(
            target,
            ["X", str(self.pacmap.pacman.lives - 1)],
            pos.x + MainData.cell_size * 3,
            pos.y,
            font,
            block_spacing=MainData.cell_size * 3,
        )
    right_top = (
        Pos2D(
            0.25,
            len(self.pacmap.cells[0]),
        )
        * MainData.cell_size
        * 3
    ) + offset
    draw_text_multiline(
        target,
        [char for char in "Score"],
        *right_top,
        font,
        block_spacing=MainData.cell_size * 3,
    )
    draw_text_multiline(
        target,
        [char for char in f"{self.pacmap.score:05}"],
        *(right_top + (0, MainData.cell_size * 3)),
        font,
        block_spacing=MainData.cell_size * 3,
        color=(pygame.color.THECOLORS["yellow"]),
    )


def replace(globals: dict):
    print("\033[2D\033[K", end="", flush=True)
    Visualizer.draw_hud.__code__ = draw_hud.__code__

    # src.ai.training.evaluate.__code__ = evaluate.__code__
    # globals["MainData"].cell_size =8
