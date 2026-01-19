from __future__ import annotations
from pathlib import Path
from typing import Dict, Any
import json

from config_loader import load_config, StrategySpec
from synthetic_market import labeled_scenarios
from strategy_registry import discover_handlers

def run_from_config(config_path: str, n_ticks: int = 3000) -> Dict[str, Any]:
    spec: StrategySpec = load_config(config_path)
    handlers = discover_handlers()

    if spec.type not in handlers:
        raise ValueError(
            f"Unknown strategy.type='{spec.type}'. "
            f"Available types: {sorted(handlers.keys())}"
        )

    handler = handlers[spec.type].load()
    df = labeled_scenarios(n=n_ticks)

    result = handler(spec, df)
    result["config_path"] = str(Path(config_path).resolve())
    result["n_ticks"] = int(n_ticks)
    return result

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, help="Path to strategy YAML/JSON")
    ap.add_argument("--n_ticks", type=int, default=3000)
    args = ap.parse_args()
    out = run_from_config(args.config, n_ticks=args.n_ticks)
    print(json.dumps(out, ensure_ascii=False, indent=2))
