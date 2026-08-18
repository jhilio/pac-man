
import json
from pathlib import Path
import sys
import mazegenerator
import pygame
from src.enums import Direction
from src.pacmap import PacMap
from src.visualizer import Visualizer
from src.config import Config

class ConfigError(Exception):
    pass


DEFAULT_CONFIG = {
    "lives": 3,
    "seed": 0,
    "width": 10,
    "height": 10,
}

def load_config(path:str):
    config = DEFAULT_CONFIG
    with open(path, "r") as config_file:
        text = config_file.read()
        text = "\n".join(line for line in text.splitlines() if not line.startswith("#"))
        loaded = json.loads(text)
        if isinstance(loaded, dict):
            loaded = {k:v for k, v in loaded.items() if k in config}
            config.update(loaded)
        else:
            raise ConfigError("config is not a dict")
    for k, v in config.items():
        Config.config_from_file[k] = v



def preload_assets():
    maze_assets = [
        "assets/maze/very_small_corner_ne.png",
        "assets/maze/very_small_corner_se.png",
        "assets/maze/very_small_corner_sw.png",
        "assets/maze/very_small_corner_nw.png",
        "assets/maze/small_corner_ne.png",
        "assets/maze/small_corner_se.png",
        "assets/maze/small_corner_sw.png",
        "assets/maze/small_corner_nw.png",
        "assets/maze/corner_ne.png",
        "assets/maze/corner_se.png",
        "assets/maze/corner_sw.png",
        "assets/maze/corner_nw.png",
        "assets/maze/double_top.png",
        "assets/maze/double_right.png",
        "assets/maze/double_left.png",
        "assets/maze/double_bottom.png",
        "assets/maze/no_dot.png",
        "assets/maze/small_dot.png",
        "assets/maze/middle_dot.png",
        "assets/maze/big_dot.png",
    ]

    pacman_anim_frames = [f"assets/pacman/pacman_frame_{num}.png" for num in range(4)]
    blinky_anim_frames = [f"assets/ghost/blinky/blinky_{direc.to_text()}{num}.png" for num in [1, 2] for direc in Direction]

    total = maze_assets + pacman_anim_frames + blinky_anim_frames
    for full_path in total:
        Config.assets.load(Path(full_path).name, full_path, pygame.Color(0, 0, 0))
        print(f"loaded {Path(full_path).name}")

def main():
    if sys.argv:
        load_config(sys.argv[1])
    else:
        print("need path of config as arg")
        return
    preload_assets()
    print("\n\n")
    size = (Config.config_from_file["width"], Config.config_from_file["height"])
    maze = mazegenerator.MazeGenerator(size=size, seed=Config.config_from_file["seed"])
    map = PacMap(maze)

    print("\n\n\n\n\n\n"+str(map))
    vis =Visualizer(map, (1500, 1500))

if __name__ == "__main__":
    main()
