import inspect
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from pygame.color import THECOLORS


from src.visualizer.visualizer import (
    Visualizer,
    MainData,
    Surface,
    draw_text_multiline,
    init_cells_from_2d,
    Pos2D,
    pygame
 )

imported = Visualizer.draw_high_scores

# imported = None


def empty() -> None:
    pass


@dataclass
class FuncRef:
    func: Callable
    filename: str
    start: int
    end: int
    name: str
    indent: int


def save_ref(func: Callable) -> FuncRef:
    """save curent state of a function
    Args:
        func (Callable): function to save
    Raises:
        ValueError: if the source of function cant be found
    Returns:
        FuncRef: the saved state
    """
    lines, start = inspect.getsourcelines(func)
    filename = inspect.getsourcefile(func)
    if filename is None:
        raise ValueError(f"Could not find source for {func}")
    indent = len(lines[0]) - len(lines[0].lstrip())
    return FuncRef(
        func=func,
        filename=filename,
        start=start,
        end=start + len(lines),
        name=func.__name__,
        indent=indent,
    )


def copy_func(src: FuncRef, dest: FuncRef) -> None:
    """copy one function to another using funcref data
    it copies everything except name
    Args:
        src (FuncRef): func to copy
        dest (FuncRef): destination func
    """
    src_lines = Path(src.filename).read_text().splitlines(keepends=True)
    dest_lines = Path(dest.filename).read_text().splitlines(keepends=True)
    copied = src_lines[src.start - 1: src.end - 1]

    src_indent = " " * src.indent
    dest_indent = " " * dest.indent
    copied = [
        dest_indent + line[len(src_indent):] if line.strip() else line
        for line in copied
    ]
    # Keep destination's original name.
    copied[0] = copied[0].replace(
        src.name,
        dest.name,
        1,
    )
    dest_lines[dest.start - 1: dest.end - 1] = copied
    Path(dest.filename).write_text("".join(dest_lines))


def my_copy(self, target:Surface, offset: Pos2D) -> None:
    font = self.get_font(MainData.cell_size*3)
    m_font = self.get_font(int(MainData.cell_size*3.75))
    big_font = self.get_font(int(MainData.cell_size*4.5))
    list_top = list(MainData.high_scores.items())
    for i, (name, score) in enumerate(list_top[3:10], 6):
        pos = offset + (Pos2D(0.25, i+0.25 )*MainData.cell_size *3 )
        draw_text_multiline(target, [char for char in f"{i-2:02}:{name}"], int(pos.x), int(pos.y), font, block_spacing=MainData.cell_size*3)
        pos_score = pos + (Pos2D(16, 0) * MainData.cell_size * 3)
        draw_text_multiline(target, [char for char in format(score, "06")], int(pos_score.x), int(pos_score.y), font, block_spacing=MainData.cell_size*3, color=pygame.color.THECOLORS["yellow"])
        
    for x, y, index, font in [(0, 3, 1, m_font), (16, 4, 2, font)]:
        name =list_top[index][0]
        if len(name) > 6:
            name = name[:5] + "-\n" + name[5:]
        #name += f"\n{list_top[index][1]:06}"
        y -= name.count("\n")
        pos = offset + (Pos2D(x +0.25, y) * MainData.cell_size *3)
        draw_text_multiline(target, [char for char in name], int(pos.x), int(pos.y), font, block_spacing=MainData.cell_size*3, line_spacing=(MainData.cell_size *3))
        score_pos = pos + (Pos2D(0, 1+name.count("\n")) * MainData.cell_size *3)
        draw_text_multiline(target, [char for char in f"{list_top[index][1]:06}"], int(score_pos.x), int(score_pos.y), font, block_spacing=MainData.cell_size*3, line_spacing=(MainData.cell_size *3), color=pygame.color.THECOLORS["yellow"])
    pos = offset + (Pos2D(6, 1) * MainData.cell_size *3)
    
    draw_text_multiline(target, [char for char in list_top[0][0]], int(pos.x), int(pos.y), big_font,block_spacing=MainData.cell_size*3)
    score_pos = pos + (Pos2D(0, 1) * MainData.cell_size *3)
    draw_text_multiline(target, [char for char in f"{list_top[0][1]:010}"], int(score_pos.x), int(score_pos.y), big_font,block_spacing=MainData.cell_size*3)

def replace(globals: dict) -> None:
    """
    used to copy -> modify -> replace function code during execution,
    then if wanted apply the patch to original func
    Args:
        globals (dict): dict of global from main
    Raises:
        KeyboardInterrupt: if imported is None
        KeyboardInterrupt: if input is not a supported action
    """
    if imported is None:
        raise KeyboardInterrupt
    if globals.get("originale_func") is None:
        globals["originale_func"] = save_ref(imported)
        globals["originale_copy"] = save_ref(my_copy)
    try:
        val = int(input("1: copy\n2: test\n3: push\n4: clear_cache\naction: "))
    except (ValueError, EOFError):
        raise KeyboardInterrupt
    if val == 1:
        copy_func(globals["originale_func"], globals["originale_copy"])
    elif val == 2:
        imported.__code__ = my_copy.__code__
    elif val == 3:
        copy_func(save_ref(my_copy), globals["originale_func"])
    elif val == 4:
        globals["originale_func"] = None
        copy_func(save_ref(empty), save_ref(my_copy))
        globals["originale_copy"] = None
    else:
        raise KeyboardInterrupt
