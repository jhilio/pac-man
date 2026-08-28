from src.visualizer.visualizer import *

import importlib

def draw_charachters2(
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
    if self.pacmap.pacman.lives <= 6:
        for x in range(self.pacmap.pacman.lives - 1):
            pos = (
                Pos2D(
                    len(self.pacmap.cells) - 1 - x, len(self.pacmap.cells[0])
                )
                * 3
                + (1, 1)
            ) * MainData.cell_size
            target.blit(self.pacmap.pacman.raw_image, pos + offset)
    else:
        offset_x = 2
        pos = (
            Pos2D(
                len(self.pacmap.cells) - 1 - offset_x, len(self.pacmap.cells[0])
            )
            * 3
            + (0.75, 0.75)
        ) * MainData.cell_size + offset
        target.blit(self.pacmap.pacman.raw_image, pos)
        #draw_text_multiline(target, "*uhi;adshuid",pos.x, pos.y, self.get_font(25))
        draw_text_multiline(target, "*",pos.x + MainData.cell_size*3, pos.y, self.get_font(40))
        draw_text_multiline(target, str(self.pacmap.pacman.lives-1),pos.x + MainData.cell_size*6, pos.y, self.get_font(40))

def replace(globals: dict):
    print("\033[2D\033[K", end="", flush=True)
    Visualizer.draw_charachters.__code__ = draw_charachters2.__code__


    # src.ai.training.evaluate.__code__ = evaluate.__code__
    #globals["MainData"].cell_size =8
