
import json, time
from pathlib import Path

def decide(regime_stats):
    reg = regime_stats.get("current_regime", "calm_trend")
    if reg == "calm_trend":
        return {"validator": "EWMA", "params": {"alpha": 0.05, "z": 2.5},
                "reason": "Low volatility upward drift; EWMA z-threshold is effective."}
    elif reg == "volatile":
        return {"validator": "Volatility", "params": {"window": 50, "max_vol": 0.03},
                "reason": "Volatility spike detected; trade only in low-vol windows."}
    else:
        return {"validator": "Persistence", "params": {"hold": 3, "thresh": 0.0},
                "reason": "Jumps/flickers present; require signal persistence across ticks."}

def log_decision(decision, metrics):
    log = {
        "timestamp": int(time.time()),
        "metrics": metrics,
        "decision": decision["validator"],
        "params": decision["params"],
        "reason": decision["reason"]
    }
    Path("../aws").mkdir(exist_ok=True)
    with open("../aws/reasoning_logs.jsonl", "a") as f:
        f.write(json.dumps(log) + "\n")
    return log
