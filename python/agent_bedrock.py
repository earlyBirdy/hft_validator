import json
import random

# Mocked Bedrock agent for hackathon demo
# In real AWS use case, replace with boto3 client for BedrockRuntime

PROMPT_TEMPLATE = """
You are a trading validation agent. You receive recent metrics and must choose which validator to use and parameters.

Metrics: {metrics}

Return JSON with fields: validator, params, reason.
"""

def run_agent(metrics):
    # Instead of calling Bedrock, we just return a random choice for demo
    choices = [
        {"validator": "EWMA", "params": {"alpha": 0.05, "threshold": 2.5}, "reason": "stable trend"},
        {"validator": "Volatility", "params": {"window": 50, "maxVol": 0.05}, "reason": "low volatility"},
        {"validator": "Persistence", "params": {"holdTicks": 3}, "reason": "persistent signal"}
    ]
    decision = random.choice(choices)
    return decision

if __name__ == "__main__":
    sample_metrics = {"sharpe": 1.2, "drawdown": 0.05}
    decision = run_agent(sample_metrics)
    with open("config.json", "w") as f:
        json.dump(decision, f, indent=2)
    print("Agent decision written to config.json:", decision)
