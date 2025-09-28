import os, subprocess, json
from datetime import datetime
from core.metrics.metrics import Metrics

def select_agent():
    impl = os.environ.get("AGENT_IMPL", "local").lower()
    if impl == "bedrock":
        from agents.bedrock_agent.agent import decide
    else:
        from agents.local_agent.agent import decide
    return decide

def main():
    decide = select_agent()
    decision = decide({"timestamp": datetime.utcnow().isoformat()})
    params = decision["params"]; validator = decision["validator"]
    data_path = os.environ.get("DATA_PATH", "data/sample_prices.csv")
    cpp_bin = os.environ.get("CPP_BIN", "cpp/backtester")
    cmd = [cpp_bin, f"--data={data_path}", f"--validator={validator}",
           f"--alpha={params.get('alpha',0.05)}", f"--threshold={params.get('threshold',2.5)}",
           f"--window={params.get('window',50)}"]
    out = subprocess.check_output(cmd).decode().strip()
    metrics = Metrics.from_cpp_json(out)
    print(json.dumps({"decision": decision, "metrics": metrics.to_dict()}, indent=2))

if __name__ == "__main__":
    main()
