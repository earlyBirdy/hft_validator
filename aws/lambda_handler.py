import json
from python import agent_bedrock

def lambda_handler(event, context):
    metrics = event.get("metrics", {})
    decision = agent_bedrock.run_agent(metrics)
    return {"statusCode": 200, "headers": {"Content-Type": "application/json"}, "body": json.dumps({"decision": decision})}
