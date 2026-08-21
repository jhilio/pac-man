import sys
import os

from src.config import MainData
import json
from pathlib import Path
import mazegenerator
from src.enums import Direction
from src.pacmap import PacMap
from src.visualizer import Visualizer
from copy import deepcopy
from typing import Optional

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"


class ConfigError(Exception):
    pass


def resource_path(relative_path: str) -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / relative_path
    return Path(__file__).resolve().parent / relative_path


levels = (
    [
        {
            "frightened_duration": 5,
            "ghost_speed": 75,
            "ghost_fright_speed": 50,
            "pacman_speed": 80,
            "pacman_fright_speed": 90,
            "duration": 90,
            "phases": [
                ["scatter", 7],
                ["chase", 20],
                ["scatter", 7],
                ["chase", 20],
                ["scatter", 5],
                ["chase", 20],
                ["scatter", 5],
                ["chase", None],
            ],
        }
    ]
    + [
        {
            "frightened_duration": 5,
            "ghost_speed": 85,
            "ghost_fright_speed": 55,
            "pacman_speed": 90,
            "pacman_fright_speed": 95,
            "duration": 90,
            "phases": [
                ["scatter", 7],
                ["chase", 20],
                ["scatter", 7],
                ["chase", 20],
                ["scatter", 5],
                ["chase", 1033],
                ["scatter", 1],
                ["chase", None],
            ],
        }
        for _ in range(3)
    ]
    + [
        {
            "frightened_duration": 5,
            "ghost_speed": 95,
            "ghost_fright_speed": 60,
            "pacman_speed": 100,
            "pacman_fright_speed": 100,
            "duration": 90,
            "phases": [
                ["scatter", 5],
                ["chase", 20],
                ["scatter", 5],
                ["chase", 20],
                ["scatter", 5],
                ["chase", 1033],
                ["scatter", 1],
                ["chase", None],
            ],
        }
        for _ in range(16)
    ]
)
levels_dict = {str(i): level for i, level in enumerate(levels, 1)}

DEFAULT_CONFIG = {
    "lives": 3,
    "seed": 0,
    "width": 15,
    "height": 15,
    "points_per_pacgum": 10,
    "points_per_super_pacgum": 50,
    "points_per_ghost": 50,
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


def load_config(path: Optional[str] = None):
    if path is not None:
        with open(path, "r") as config_file:
            text = config_file.read()
            text = "\n".join(
                line for line in text.splitlines() if not line.startswith("#")
            )
            loaded = json.loads(text)
        if not isinstance(loaded, dict):
            raise ConfigError("config is not a dict")
    else:
        loaded = {}
    config = merge_config(deepcopy(DEFAULT_CONFIG), loaded)
    for k, v in config.items():
        MainData.config_from_file[k] = v


def preload_assets(verbose: bool = False):
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
        "assets/ghost/eyes/eyes_w.png",
    ]
    frightened_assets = [
        "assets/ghost/frightened/frightened_1.png",
        "assets/ghost/frightened/frightened_2.png",
        "assets/ghost/frightened/frightened_flash_1.png",
        "assets/ghost/frightened/frightened_flash_2.png",
    ]
    pacman_anim_frames = [
        f"assets/pacman/pacman_frame_{num}.png" for num in range(4)
    ]
    ghosts_anim_frames = [
        f"assets/ghost/{name}/{name}_{direc.to_text()}{num}.png"
        for num in [1, 2]
        for direc in Direction
        for name in ["pinky", "blinky", "inky", "clyde"]
    ]
    asset_menu = [
        "assets/menu/BGmenu.jpg",
        "assets/menu/back.png",
        "assets/menu/unpaused.png",
        "assets/menu/paused.png",
        ]
    total = (
        maze_assets
        + pacman_anim_frames
        + ghosts_anim_frames
        + eyes_assets
        + frightened_assets
        + asset_menu
    )

    for full_path in total:
        MainData.assets.load(
            resource_path(full_path).name,
            str(resource_path(full_path)),
            (0, 0, 0),
        )
        if verbose:
            print(f"loaded {Path(full_path).name}")


def load_high_scores(verbose: bool = False):
    with open("high_scores.json") as file:
        loaded = json.load(file)
    if verbose:
        print(loaded)
    if not isinstance(loaded, dict):
        raise ConfigError("high score should be a dict")
    for k, v in loaded.items():
        if not isinstance(k, str) or not isinstance(v, int):
            raise ConfigError("high score should be a dict of {str: int}")
        if k == "":
            raise ConfigError("high score name should not be empty")
        if v < 0:
            raise ConfigError("high score value should not be negative")
    MainData.high_scores = loaded


def main():
    verbose = "verbose" in sys.argv
    if len(sys.argv) > 1 + ("verbose" in sys.argv):
        if sys.argv[1] == "":
            load_config()
            print("no config provided, using default values")
        else:
            load_config(sys.argv[1])
    else:
        load_config()
        print("no config provided, using default values")
    if verbose:
        print(json.dumps(MainData.config_from_file, indent=2))
    load_high_scores(verbose=verbose)
    preload_assets(verbose=verbose)
    size = (
        MainData.config_from_file["width"],
        MainData.config_from_file["height"],
    )
    maze = mazegenerator.MazeGenerator(
        size=size, seed=MainData.config_from_file["seed"]
    )
    PacMap(maze)
    MainData.visualizer = Visualizer(
        MainData.pacmap, (1400, 1100), verbose=verbose
    )
    MainData.visualizer.launch_loop()


if __name__ == "__main__":
    main()
