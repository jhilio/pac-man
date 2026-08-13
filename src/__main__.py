
import json
import sys
import mazegenerator

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
	maze =mazegenerator.MazeGenerator(size=(config["width"], config["height"]), seed=config["seed"])
	maze.generate()
	hexa = "\n".join(
            " ".join(hex(maze.maze[y][x])[2:] for
                    x in range(config["width"]))
            for y in range(config["height"])
        )
	print(hexa)
	print(config)

if __name__ == "__main__":
	main()