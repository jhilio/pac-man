from typing import Callable


from src.visualizer.visualizer import  Visualizer
import ast
import inspect
import textwrap
imported = Visualizer.draw_hud

def copy_func(src, dest):
    src_source = textwrap.dedent(inspect.getsource(src))
    dest_source = textwrap.dedent(inspect.getsource(dest))
    src_tree = ast.parse(src_source)
    dest_tree = ast.parse(dest_source)
    src_func = src_tree.body[0]
    dest_func = dest_tree.body[0]
    # Copy the source function's body into the destination.
    dest_func.body = src_func.body

    print(ast.unparse(dest_tree))


def my_copy():
    pass

def replace(globals: dict):

    copy_func(imported, my_copy)
    imported.__code__ = my_copy.__code__

    # src.ai.training.evaluate.__code__ = evaluate.__code__
    # globals["MainData"].cell_size =8
