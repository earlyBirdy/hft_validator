import json
from agent_bedrock import run_agent

def lambda_handler(event, context):
    metrics = event.get("metrics", {"sharpe": 1.0, "drawdown": 0.1})
    decision = run_agent(metrics)
    return {
        "statusCode": 200,
        "body": json.dumps(decision)
    }
