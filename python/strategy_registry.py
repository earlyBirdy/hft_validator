from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Dict, Any
from pathlib import Path
import importlib
import re

@dataclass(frozen=True)
class StrategyHandler:
    type: str
    module: str
    func: str = "run"

    def load(self) -> Callable[..., Dict[str, Any]]:
        mod = importlib.import_module(self.module)
        fn = getattr(mod, self.func, None)
        if fn is None or not callable(fn):
            raise TypeError(f"{self.module}.{self.func} not found/callable")
        return fn

def discover_handlers() -> Dict[str, StrategyHandler]:
    """Auto-discover python/strategy_impl_*.py and map type -> module.run."""
    base = Path(__file__).resolve().parent
    handlers: Dict[str, StrategyHandler] = {}
    for p in base.glob("strategy_impl_*.py"):
        m = re.match(r"strategy_impl_(.+)\.py$", p.name)
        if not m:
            continue
        stype = m.group(1)
        handlers[stype] = StrategyHandler(type=stype, module=p.stem, func="run")
    return handlers
