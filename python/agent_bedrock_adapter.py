# python/agent_bedrock_adapter.py
# Exposes a uniform run_agent(metrics) by adapting whatever is defined in python.agent_bedrock

import json

def run_agent(metrics):
    try:
        # Import inside the function so edits to python/agent_bedrock.py are reloaded on restart
        import importlib
        m = importlib.import_module("python.agent_bedrock")
    except Exception as exc:
        return {
            "validator": "EWMA",
            "params": {"alpha": 0.05},
            "reason": f"Adapter import error: {exc!r}"
        }

    # 1) Direct run_agent
    fn = getattr(m, "run_agent", None)
    if callable(fn):
        try:
            return fn(metrics)
        except Exception as exc:
            return {"validator": "EWMA", "params": {"alpha": 0.05}, "reason": f"run_agent error: {exc!r}"}

    # 2) decide(metrics)
    fn = getattr(m, "decide", None)
    if callable(fn):
        try:
            return fn(metrics)
        except Exception as exc:
            return {"validator": "EWMA", "params": {"alpha": 0.05}, "reason": f"decide error: {exc!r}"}

    # 3) lambda_handler(event, context)
    fn = getattr(m, "lambda_handler", None)
    if callable(fn):
        try:
            res = fn({"metrics": metrics}, None)
            # normalize common lambda shapes
            if isinstance(res, dict):
                if "body" in res:
                    try:
                        body = res["body"]
                        if isinstance(body, (bytes, bytearray)):
                            body = body.decode("utf-8", "replace")
                        body = json.loads(body) if isinstance(body, str) else body
                        return body.get("decision", body)
                    except Exception:
                        return {"validator": "EWMA", "params": {"alpha": 0.05}, "reason": "lambda_handler returned non-JSON body"}
                return res
        except Exception as exc:
            return {"validator": "EWMA", "params": {"alpha": 0.05}, "reason": f"lambda_handler error: {exc!r}"}

    # 4) Class with run / decide
    for cls_name in ("Agent", "BedrockAgent", "HFTAgent"):
        C = getattr(m, cls_name, None)
        if C:
            try:
                inst = C()
                for meth in ("run", "decide", "run_agent"):
                    meth_fn = getattr(inst, meth, None)
                    if callable(meth_fn):
                        try:
                            return meth_fn(metrics)
                        except Exception as exc:
                            return {"validator": "EWMA", "params": {"alpha": 0.05}, "reason": f'{cls_name}.{meth} error: {exc!r}'}
            except Exception as exc:
                return {"validator": "EWMA", "params": {"alpha": 0.05}, "reason": f'Instantiate {cls_name} error: {exc!r}'}

    # 5) Fallback
    return {
        "validator": "EWMA",
        "params": {"alpha": 0.05},
        "reason": "No compatible entrypoint found in python.agent_bedrock"
    }
