# agents/bedrock_agent/agent.py
# Wrapper that uses the adapter to expose a stable decide(metrics) for the UI
try:
    from python.agent_bedrock_adapter import run_agent as _run_agent
    _IMPORT_ERR = None
except Exception as exc:
    _IMPORT_ERR = repr(exc)
    def _run_agent(metrics):
        return {
            "validator": "EWMA",
            "params": {"alpha": 0.05},
            "reason": f"Wrapper adapter import error: {_IMPORT_ERR}"
        }

def decide(metrics):
    return _run_agent(metrics)
