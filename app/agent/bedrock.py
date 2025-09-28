import os, json
def decide(context: dict)->dict:
    if os.environ.get("USE_BEDROCK","0")!="1":
        return {"hint_strategy":"EWMA","hint_params":{"alpha":0.05,"threshold":2.5,"window":50},"reason":"Fallback (USE_BEDROCK=0)"}
    model_id=os.environ.get("BEDROCK_MODEL_ID","amazon.nova-micro-v1:0")
    try:
        import boto3
        client=boto3.client("bedrock-runtime", region_name=os.environ.get("AWS_REGION","us-east-1"))
        prompt={"instruction":"Suggest strategy (EWMA/PERSIST) with params for better Sharpe.","context":context}
        body=json.dumps({"inputText": json.dumps(prompt), "textGenerationConfig":{"temperature":0.2,"maxTokenCount":300}})
        resp=client.invoke_model(modelId=model_id, body=body)
        payload=resp.get("body").read().decode("utf-8")
        try: parsed=json.loads(payload)
        except Exception: parsed={}
        if "strategy" in parsed or "params" in parsed:
            return {"hint_strategy": parsed.get("strategy","EWMA"),
                    "hint_params": parsed.get("params", {}),
                    "reason": f"Bedrock({model_id}) hint"}
        return {"hint_strategy":"EWMA","hint_params":{"alpha":0.05,"threshold":2.5,"window":50},"reason":f"Bedrock({model_id}) default"}
    except Exception as e:
        return {"hint_strategy":"EWMA","hint_params":{"alpha":0.05,"threshold":2.5,"window":50},"reason":f"Bedrock error: {e}"}
