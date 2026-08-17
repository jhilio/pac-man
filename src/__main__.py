
import json
import sys
import mazegenerator
from .pacmap import PacMap
from .visualizer import Visualizer

class ConfigError(Exception):
	pass


DEFAULT_CONFIG = {
	"lives": 1,
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
	return config


def main():
	if sys.argv:
		config = load_config(sys.argv[1])
	else:
		print("need path of config as arg")
		return
	maze = mazegenerator.MazeGenerator(size=(config["width"], config["height"]), seed=config["seed"])
	map = PacMap(maze)

	print("\n\n\n\n\n\n"+str(map))
	vis =Visualizer(map, (1500, 1500))

if __name__ == "__main__":
	main()