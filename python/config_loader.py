from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Union
import json

try:
    import yaml  # PyYAML
except Exception:
    yaml = None

ConfigDict = Dict[str, Any]

@dataclass(frozen=True)
class StrategySpec:
    raw: ConfigDict
    path: str

    @property
    def id(self) -> str:
        return self.raw.get("strategy", {}).get("id", "unknown_strategy")

    @property
    def name(self) -> str:
        return self.raw.get("strategy", {}).get("name", self.id)

    @property
    def type(self) -> str:
        # e.g., "kd_cross"
        return self.raw.get("strategy", {}).get("type", "unknown")

def load_config(path: Union[str, Path]) -> StrategySpec:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Config not found: {p}")
    ext = p.suffix.lower()

    if ext in [".yaml", ".yml"]:
        if yaml is None:
            raise RuntimeError("PyYAML not installed. Run: pip install pyyaml")
        raw = yaml.safe_load(p.read_text(encoding="utf-8"))
    elif ext == ".json":
        raw = json.loads(p.read_text(encoding="utf-8"))
    else:
        raise ValueError(f"Unsupported config extension: {ext}")

    if not isinstance(raw, dict):
        raise ValueError("Config root must be an object/dict")
    return StrategySpec(raw=raw, path=str(p))

def get_exec_params(spec: StrategySpec) -> ConfigDict:
    r = spec.raw
    pos = r.get("position", {}).get("sizing", {})
    kd = r.get("indicator", {}).get("kd", {})
    thresh = r.get("filters", {}).get("thresholds", {})
    sess = r.get("session", {})
    exec_ = r.get("execution", {})

    return {
        "instrument": r.get("strategy", {}).get("instrument", {}),
        "kd": {
            "k_period": kd.get("k_period", 9),
            "d_period": kd.get("d_period", 3),
            "smooth": kd.get("smooth", 3),
            "source": kd.get("source", "close"),
        },
        "thresholds": {
            "oversold": thresh.get("oversold", 20),
            "overbought": thresh.get("overbought", 80),
        },
        "session": {
            "start": sess.get("entry_window", {}).get("start", "09:00"),
            "end": sess.get("entry_window", {}).get("end", "10:00"),
            "force_flat": sess.get("force_flat", {}).get("time", "10:00"),
        },
        "position": {
            "initial_size": pos.get("initial_size", 1),
            "add_size": pos.get("add_size", 1),
            "max_position": pos.get("max_position", 4),
            "allow_pyramiding": pos.get("allow_pyramiding", True),
        },
        "reverse_mode": exec_.get("reverse_handling", {}).get("mode", "flatten_then_reverse"),
        "same_bar_reverse": exec_.get("reverse_handling", {}).get("same_bar_reverse", True),
    }
