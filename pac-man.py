from src.config import MainData
import json
from pathlib import Path
import sys
import mazegenerator
from src.enums import Direction
from src.pacmap import PacMap
from src.visualizer import Visualizer
from copy import deepcopy

class ConfigError(Exception):
    pass

levels = (
    [
        {
            "ghost_speed": 75,
            "ghost_fright_speed": 50,
            "pacman_speed": 80,
            "pacman_fright_speed": 90,
            "duration": 90
        }
    ]
    + [
        {
            "ghost_speed": 85,
            "ghost_fright_speed": 55,
            "pacman_speed": 90,
            "pacman_fright_speed": 95,
            "duration": 90
        }
        for _ in range(3)
    ]
    + [
        {
            "ghost_speed": 95,
            "ghost_fright_speed": 60,
            "pacman_speed": 100,
            "pacman_fright_speed": 100,
            "duration": 90
        }
        for _ in range(16)
    ]
)
levels_dict = {str(i): level for i, level in enumerate(levels, 1)}

DEFAULT_CONFIG = {
    "lives": 3,
    "seed": 0,
    "width": 10,
    "height": 10,
    "pac_gum_point": 10,
    "superpac_gum_point": 50,
    "levels": levels_dict,
}


def merge_config(default, override):
    for key, value in override.items():
        if key not in default:
            continue
        if not isinstance(value, type(default[key])):
            raise ConfigError(f"wrong type of  value for key {key} : {value}")

        if isinstance(value, dict):
            default[key] = merge_config(default[key], value)
        else:
            default[key] = value
    return default

def load_config(path: str):
    with open(path, "r") as config_file:
        text = config_file.read()
        text = "\n".join(line for line in text.splitlines() if not line.startswith("#"))
        loaded = json.loads(text)
    if not isinstance(loaded, dict):
        raise ConfigError("config is not a dict")

    config = merge_config(deepcopy(DEFAULT_CONFIG), loaded)
    for k, v in config.items():
        MainData.config_from_file[k] = v


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

    eyes_assets = [
        "assets/ghost/eyes/eyes_n.png",
        "assets/ghost/eyes/eyes_e.png",
        "assets/ghost/eyes/eyes_s.png",
        "assets/ghost/eyes/eyes_w.png"
    ]
    pacman_anim_frames = [f"assets/pacman/pacman_frame_{num}.png" for num in range(4)]
    ghosts_anim_frames = [
        f"assets/ghost/{name}/{name}_{direc.to_text()}{num}.png"
        for num in [1, 2]
        for direc in Direction
        for name in ["pinky", "blinky", "inky", "clyde"]
    ]


    total = (maze_assets + pacman_anim_frames + ghosts_anim_frames + eyes_assets)
    for full_path in total:
        MainData.assets.load(Path(full_path).name, full_path, (0, 0, 0))
        print(f"loaded {Path(full_path).name}")


def main():
    if sys.argv:
        load_config(sys.argv[1])
        print(json.dumps(MainData.config_from_file, indent=2))
    else:
        print("need path of MainData as arg")
        return
    preload_assets()
    print("\n\n")
    size = (MainData.config_from_file["width"], MainData.config_from_file["height"])
    maze = mazegenerator.MazeGenerator(size=size, seed=MainData.config_from_file["seed"])
    PacMap(maze)
    vis = Visualizer(MainData.pacmap, (1400, 1100))


if __name__ == "__main__":
    main()
