import importlib
import json
import os
import signal
import sys
from copy import deepcopy
from pathlib import Path
from typing import Optional

import mazegenerator

import src.reloader
from src.ai.interface import NNDirectionChooser
from src.ai.network import PacmanNetwork
from src.config import MainData
from src.enums import Direction
from src.pacmap import PacMap
from src.visualizer.visualizer import Visualizer

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"


def reload_handler(signum, frame):
    print("\033[2D\033[K", end="", flush=True)
    try:
        importlib.reload(src.reloader)
        src.reloader.replace(globals())
    except Exception as error:
        print(f"couldnt reload the reloader :{error}")

signal.signal(signal.SIGINT, reload_handler)


class ConfigError(Exception):
    pass


def resource_path(relative_path: str) -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / relative_path
    return Path(__file__).resolve().parent / relative_path


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
    merge_config(MainData.config_from_file, loaded)


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
        "assets/menu/leftbg.png",
        "assets/menu/rightbg.png",
        "assets/menu/gameback.png",
        "assets/menu/button.png",
        "assets/menu/control.png",
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
    try:
        with open(str(resource_path("high_scores.json"))) as file:
            loaded = json.load(file)
    except Exception as e:
        print(
            f"couldnt open high_scores.json : {e}\n Defaulting to empty high scores"
        )
        loaded = {}
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


def clamp_config():
    config = MainData.config_from_file
    clamp_dict = {
        "lives": (1, 10),
        "width": (15, 25),
        "height": (15, 25),
        "points_per_pacgum": (1, 1000),
        "points_per_super_pacgum": (1, 1000),
        "points_per_ghost": (1, 1000),
    }
    for key, (minimum, maximum) in clamp_dict.items():
        clamped = min(max(config[key], minimum), maximum)

        if clamped != config[key]:
            print(
                f"invalid value {config[key]} for {key}, "
                f"defaulting to safe value {clamped}"
            )
            config[key] = clamped
    level_clamp_dict = {
        "frightened_duration": (1, 10),
        "ghost_speed": (1, 200),
        "ghost_fright_speed": (1, 200),
        "pacman_speed": (1, 300),
        "pacman_fright_speed": (1, 300),
        "duration": (30, 3600),
    }
    for level_num, level in config["levels"].items():
        for key, (minimum, maximum) in level_clamp_dict.items():
            clamped = min(max(level[key], minimum), maximum)

            if clamped != level[key]:
                print(
                    f"invalid value {level[key]} for level {level_num} "
                    f"at key {key}, defaulting to safe value {clamped}"
                )
                level[key] = clamped

        if not any(phase == ["chase", None] for phase in level["phases"]):
            print(
                f"couldnt find eternal chase at end of phases, defaulting to permanent chase"
            )
            level["phases"] = [["chase", None]]


def main():
    verbose = "verbose" in sys.argv
    try:
        if len(sys.argv) > 1 + ("verbose" in sys.argv):
            if sys.argv[1] == "":
                load_config()
                print("no config provided, using default values")
            elif sys.argv[1] == "verbose":
                load_config(sys.argv[2])
            else:
                load_config(sys.argv[1])
        else:
            load_config()
            print("no config provided, using default values")
        if verbose:
            print(json.dumps(MainData.config_from_file, indent=2))

        load_high_scores(verbose=verbose)
        preload_assets(verbose=verbose)
        nn = PacmanNetwork(
            model_path=str(resource_path("models/last_result.pt"))
        )
    except (
        OSError,
        FileNotFoundError,
        IsADirectoryError,
        PermissionError,
    ) as error:
        print(f"error occured while loading config : {error}, exiting..,")
        return
    clamp_config()
    size = (
        MainData.config_from_file["width"],
        MainData.config_from_file["height"],
    )
    maze = mazegenerator.MazeGenerator(
        size=size, seed=MainData.config_from_file["seed"]
    )
    pacmap = PacMap(maze)
    chooser = NNDirectionChooser(nn)
    vis = Visualizer(pacmap, (1000, 1000), nn=chooser, verbose=verbose)
    try:
        vis.launch_loop()
    except KeyboardInterrupt:
        pass
    finally:
        with open(str(resource_path("high_scores.json")), "w") as file:
            json.dump(MainData.high_scores, file, indent=2)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
