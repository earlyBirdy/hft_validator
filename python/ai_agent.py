import json
import random

# Simple AI agent: parameter tuner
def tune_params():
    best_score = -1e9
    best = None
    for _ in range(20):
        alpha = random.uniform(0.01, 0.2)
        threshold = random.uniform(1.5, 3.5)
        score = -(abs(alpha - 0.05) + abs(threshold - 2.5)) # pretend scoring
        if score > best_score:
            best_score = score
            best = {"alpha": alpha, "threshold": threshold}
    return best

if __name__ == "__main__":
    params = tune_params()
    with open("config.json", "w") as f:
        json.dump(params, f, indent=2)
    print("Best params written to config.json:", params)
