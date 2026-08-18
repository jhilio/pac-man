
import json
import sys
import mazegenerator
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


def main():
    if sys.argv:
        load_config(sys.argv[1])
    else:
        print("need path of config as arg")
        return
    size = (Config.config_from_file["width"], Config.config_from_file["height"])
    maze = mazegenerator.MazeGenerator(size=size, seed=Config.config_from_file["seed"])
    map = PacMap(maze)

    print("\n\n\n\n\n\n"+str(map))
    vis =Visualizer(map, (1500, 1500))

if __name__ == "__main__":
    main()
