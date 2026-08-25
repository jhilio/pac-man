import src.ai.training

def evaluate(pacmap, chooser):
    return (0, 0)

def replace(globals:dict):
    src.ai.training.evaluate.__code__ = evaluate.__code__
    print("worked")
