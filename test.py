import json

with open("save_text_2") as file:
    data = json.load(file)

step = len(data)//10

for i in range(0, len(data), step):
    data_slice = data[i:i+step]
    score_cum = 0
    steps_cum = 0
    for di in data_slice:
        score_cum += di["score"]
        steps_cum += di["steps"]
    print(f"{i}:{i+step}\n {score_cum/step}, {steps_cum/step}")
