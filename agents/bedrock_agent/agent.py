import os, json
def decide(context: dict) -> dict:
    use_bedrock = os.environ.get("USE_BEDROCK", "0") == "1"
    if not use_bedrock:
        return {"validator":"EWMA","params":{"alpha":0.05,"threshold":2.5,"window":50},"reason":"Fallback (USE_BEDROCK=0)."}
    model_id = os.environ.get("BEDROCK_MODEL_ID", "amazon.nova-micro-v1:0")
    try:
        import boto3
        client = boto3.client("bedrock-runtime", region_name=os.environ.get("AWS_REGION", "us-east-1"))
        body = json.dumps({"inputText": json.dumps({"context":context}),
                           "textGenerationConfig":{"temperature":0.2,"maxTokenCount":200}})
        resp = client.invoke_model(modelId=model_id, body=body)
        payload = resp.get("body").read().decode("utf-8")
        try:
            parsed = json.loads(payload)
            params = parsed.get("params") or parsed
            alpha = float(params.get("alpha", 0.05))
            thr = float(params.get("threshold", 2.5))
            window = int(params.get("window", 50))
        except Exception:
            alpha, thr, window = 0.05, 2.5, 50
        return {"validator":"EWMA","params":{"alpha":alpha,"threshold":thr,"window":window},"reason":f"Bedrock({model_id})."}
    except Exception as e:
        return {"validator":"EWMA","params":{"alpha":0.05,"threshold":2.5,"window":50},"reason":f"Bedrock error: {e}"}
