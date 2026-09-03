import inspect
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path


# from src.visualizer.visualizer import (
#    Visualizer,
# )

# imported = Visualizer.draw_high_scores

imported = None


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


def my_copy() -> None:
    pass


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
