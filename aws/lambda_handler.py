
import json, time, os
try:
    from agent_bedrock import run_agent
except Exception:
    def run_agent(metrics):
        return {"validator":"EWMA","params":{"alpha":0.05,"threshold":2.5},"reason":"fallback"}

def lambda_handler(event, context):
    metrics = event.get("metrics", {"sharpe": 1.0, "drawdown": 0.1})
    decision = run_agent(metrics)
    os.makedirs("/tmp", exist_ok=True)
    entry = {
        "timestamp": int(time.time()),
        "metrics": metrics,
        "decision": decision.get("validator"),
        "params": decision.get("params"),
        "reason": decision.get("reason")
    }
    with open("/tmp/reasoning_logs.jsonl", "a") as f:
        f.write(json.dumps(entry) + "\n")
    return {"statusCode": 200, "body": json.dumps(decision)}
