import json, os
def handler(event, context):
    impl = os.environ.get("AGENT_IMPL", "bedrock").lower()
    if impl == "local":
        from agents.local_agent.agent import decide
    else:
        from agents.bedrock_agent.agent import decide
    body={}
    try:
        if "body" in event and event["body"]:
            body=json.loads(event["body"]) if isinstance(event["body"],str) else event["body"]
    except Exception:
        body={}
    decision = decide({"request": body})
    return {"statusCode":200,"headers":{"Content-Type":"application/json"},"body":json.dumps({"decision":decision})}
