from random import Random


def random_map_bool(proportion: float, size: int=100):
    seed = 42
    res = [i / proportion < size  for i in range(size) ]
    Random(seed).shuffle(res)
    return res



a = random_map_bool(0.02)
print(a.count(True), a)