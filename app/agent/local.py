import os, random
def decide(context: dict)->dict:
    mode=os.environ.get("AGENT_MODE","smart")
    if mode=="fixed":
        return {"hint_strategy":"EWMA","hint_params":{"alpha":0.05,"threshold":2.5,"window":50},"reason":"Fixed defaults"}
    seed=int(os.environ.get("AGENT_SEED","1234")); random.seed(seed)
    return {"hint_strategy": random.choice(["EWMA","PERSIST"]),
            "hint_params":{"alpha":0.05,"threshold":2.5,"window":50,"hold_period":10},
            "reason":"Local smart hint"}
