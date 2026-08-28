
from src.visualizer.visualizer import  *
imported = Visualizer.draw_cells

import ast
import inspect
from pathlib import Path
import inspect
from dataclasses import dataclass
from typing import Callable

def empty():
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

def copy_func(src: FuncRef, dest: FuncRef):
    src_lines = Path(src.filename).read_text().splitlines(keepends=True)
    dest_lines = Path(dest.filename).read_text().splitlines(keepends=True)

    copied = src_lines[src.start - 1:src.end - 1]

    src_indent = " " * src.indent
    dest_indent = " " * dest.indent
    copied = [
        dest_indent + line[len(src_indent):]
        if line.strip()
        else line
        for line in copied
    ]
    # Keep destination's original name.
    copied[0] = copied[0].replace(
        src.name,
        dest.name,
        1,
    )
    dest_lines[dest.start - 1:dest.end - 1] = copied
    Path(dest.filename).write_text("".join(dest_lines))

def my_copy():
    pass


def replace(globals: dict):
    if imported is None:
        raise KeyboardInterrupt
    if globals.get("originale_func") is None:
        globals["originale_func"] = save_ref(imported)
    copy = save_ref(my_copy)
    try:
        val = int(input(
            "1: copy\n"
            "2: test\n"
            "3: push\n"
            "4: clear_cache\n"
            "action: "
        ))
    except (ValueError, EOFError):
        raise KeyboardInterrupt
    if val == 1:
        copy_func(globals["originale_func"], copy)
    elif val == 2:
        imported.__code__ = my_copy.__code__
    elif val == 3:
        copy_func(copy, globals["originale_func"])#
    elif val == 4:
        globals["originale_func"] = None
        copy_func(save_ref(empty), save_ref(my_copy))
    else:
        raise KeyboardInterrupt
    print("finished")##