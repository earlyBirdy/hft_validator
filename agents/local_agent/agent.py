import os, random
def decide(context: dict) -> dict:
    seed = int(os.environ.get("AGENT_SEED", "1234"))
    random.seed(seed)
    alpha = random.choice([0.03, 0.05, 0.08])
    thr = random.choice([2.0, 2.5, 3.0])
    window = random.choice([30, 50, 80])
    return {"validator":"EWMA","params":{"alpha":alpha,"threshold":thr,"window":window},"reason":"Local mock."}
