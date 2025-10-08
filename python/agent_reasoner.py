
import json, os, time

def decide(context):
    reg = context.get("current_regime", "calm_trend")
    if reg == "calm_trend":
        return {"validator":"EWMA","reason":"Stable upward trend with low volatility"}
    if reg == "volatile":
        return {"validator":"Volatility","reason":"Elevated return volatility; prefer volatility gate"}
    return {"validator":"Persistence","reason":"Spiky moves; require persistence above rolling mean"}

def log_decision(decision, metrics, path):
    rec = {
        "timestamp": int(time.time()),
        "decision": decision.get("validator"),
        "reason": decision.get("reason"),
        "context": metrics
    }
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(rec) + "\n")
