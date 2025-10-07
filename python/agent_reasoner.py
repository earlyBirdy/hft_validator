
import json, time, os

def decide(regime_stats):
    reg = regime_stats.get("current_regime", "calm_trend")
    if reg == "calm_trend":
        return {"validator": "EWMA", "params": {"alpha": 0.05, "z": 2.0},
                "reason": "Low volatility upward drift; EWMA z-threshold is effective."}
    elif reg == "volatile":
        return {"validator": "Volatility", "params": {"window": 50, "max_vol": 0.01},
                "reason": "Volatility spike detected; trade only in low-vol windows."}
    else:
        return {"validator": "Persistence", "params": {"hold": 2, "mean_alpha":0.05, "z": 0.15},
                "reason": "Jumps present; require persistence above rolling mean."}

def log_decision(decision, metrics, logs_path):
    os.makedirs(os.path.dirname(logs_path), exist_ok=True)
    entry = {
        "timestamp": int(time.time()),
        "metrics": metrics,
        "decision": decision["validator"],
        "params": decision["params"],
        "reason": decision["reason"]
    }
    with open(logs_path, "a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry
