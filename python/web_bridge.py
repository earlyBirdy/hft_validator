"""Streamlit integration helpers.

This module provides a thin, UI-friendly wrapper over:
- strategy discovery + execution (strategy_impl_*.py)
- validator simulation (validator_sim.py)
- data loading (synthetic + CSV)

It intentionally keeps dependencies minimal so Streamlit can import it directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
import io
import time

import numpy as np
import pandas as pd

from config_loader import StrategySpec, load_config
from strategy_registry import discover_handlers
from synthetic_market import labeled_scenarios
from validator_sim import (
    EWMAValidator,
    VolatilityValidator,
    PersistenceValidator,
    ConfirmWrapper,
    simulate,
)


def list_strategy_configs(strategies_dir: Path) -> List[Path]:
    exts = {".yaml", ".yml", ".json"}
    if not strategies_dir.exists():
        return []
    return sorted([p for p in strategies_dir.iterdir() if p.is_file() and p.suffix.lower() in exts])


def read_price_df_from_upload(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """Load a price dataframe from an uploaded CSV.

    Expected: a column named one of: price, close, Close, last, Last
    Output: DataFrame with at least a float 'price' column.
    """
    name = (filename or "uploaded.csv").lower()
    if not name.endswith(".csv"):
        raise ValueError("Only CSV uploads are supported for now.")

    df = pd.read_csv(io.BytesIO(file_bytes))
    if df.empty:
        raise ValueError("CSV appears empty.")

    # Normalize columns
    cols = {c.lower(): c for c in df.columns}
    for cand in ["price", "close", "last"]:
        if cand in cols:
            src = cols[cand]
            out = pd.DataFrame({"price": pd.to_numeric(df[src], errors="coerce")})
            out = out.dropna().reset_index(drop=True)
            if out.empty:
                raise ValueError(f"Column '{src}' contains no numeric values.")
            return out

    raise ValueError(
        "CSV must contain a numeric column named one of: price, close, last (case-insensitive)."
    )


def make_synthetic_df(n_ticks: int, seed: int = 123) -> pd.DataFrame:
    df = labeled_scenarios(n=int(n_ticks), seed=int(seed))
    return df[["price"]].copy()


def get_strategy_catalog() -> Dict[str, Dict[str, Any]]:
    """Return discovered strategy types + the module path."""
    handlers = discover_handlers()
    out: Dict[str, Dict[str, Any]] = {}
    for t, h in handlers.items():
        # Best-effort validation so the UI can surface broken modules early.
        ok = True
        err: Optional[str] = None
        try:
            _ = h.load()
        except Exception as e:
            ok = False
            err = f"{type(e).__name__}: {e}"

        out[t] = {
            "type": t,
            "module": h.module,
            "func": getattr(h, "func", "run"),
            "ok": ok,
            "error": err,
        }
    return dict(sorted(out.items(), key=lambda kv: kv[0]))


def run_strategy_on_df(spec: StrategySpec, df: pd.DataFrame) -> Dict[str, Any]:
    handlers = discover_handlers()
    if spec.type not in handlers:
        raise ValueError(
            f"Unknown strategy.type='{spec.type}'. Available types: {sorted(handlers.keys())}"
        )

    handler = handlers[spec.type].load()
    result = handler(spec, df)

    # Normalize a few fields for UI
    result.setdefault("strategy_id", spec.id)
    result.setdefault("strategy_name", spec.name)
    result.setdefault("strategy_type", spec.type)
    result["config_path"] = str(Path(spec.path).resolve())
    result["n_ticks"] = int(len(df))
    return result


def make_validator(validator_kind: str, params: Dict[str, Any]) -> Any:
    """Build a validator instance from UI choices."""
    kind = (validator_kind or "EWMA").strip().upper()

    if kind == "EWMA":
        inner = EWMAValidator(
            alpha=float(params.get("alpha", 0.05)),
            z_enter=float(params.get("z_enter", 2.5)),
            z_exit=float(params.get("z_exit", 1.8)),
        )
    elif kind == "VOLATILITY":
        inner = VolatilityValidator(
            window=int(params.get("window", 50)),
            max_vol=float(params.get("max_vol", 0.01)),
        )
    elif kind == "PERSISTENCE":
        inner = PersistenceValidator(
            hold=int(params.get("hold", 3)),
            mean_alpha=float(params.get("mean_alpha", 0.05)),
            z=float(params.get("z", 0.2)),
        )
    else:
        raise ValueError("validator_kind must be one of: EWMA, Volatility, Persistence")

    confirm = int(params.get("confirm", 1))
    if confirm and confirm > 1:
        return ConfirmWrapper(inner, confirm=confirm)
    return inner


def max_drawdown_from_equity(equity: Iterable[float]) -> float:
    eq = np.asarray(list(equity), dtype=float)
    if eq.size == 0:
        return 0.0
    peak = np.maximum.accumulate(eq)
    dd = peak - eq
    return float(np.max(dd)) if dd.size else 0.0


def run_validator_sim(df: pd.DataFrame, validator_kind: str, params: Dict[str, Any]) -> Dict[str, Any]:
    v = make_validator(validator_kind, params)
    sim_params = {
        "latency_ticks": int(params.get("latency_ticks", 1)),
        "cost_bps": float(params.get("cost_bps", 0.5)),
        "slip_bps": float(params.get("slip_bps", 0.3)),
        "position": float(params.get("position", 1.0)),
        "min_interval_ticks": int(params.get("min_interval_ticks", 5)),
        "max_trades_per_100": int(params.get("max_trades_per_100", 15)),
    }

    out = simulate(df, v, **sim_params)
    out["validator_kind"] = validator_kind
    out["max_drawdown"] = max_drawdown_from_equity(out.get("equity", []))
    out["sim_params"] = sim_params
    return out


def make_unified_row(
    *,
    timestamp: str,
    data_source: str,
    n_ticks: int,
    strategy_result: Optional[Dict[str, Any]] = None,
    validator_result: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    row: Dict[str, Any] = {
        "timestamp": timestamp,
        "data_source": data_source,
        "n_ticks": int(n_ticks),
    }

    if strategy_result:
        row.update(
            {
                "strategy_id": strategy_result.get("strategy_id"),
                "strategy_name": strategy_result.get("strategy_name"),
                "strategy_type": strategy_result.get("strategy_type"),
                "strategy_total_pnl": float(strategy_result.get("total_pnl", 0.0)),
                "strategy_trades": int(strategy_result.get("trades", 0)),
                "config_path": strategy_result.get("config_path"),
            }
        )

    if validator_result:
        row.update(
            {
                "validator_kind": validator_result.get("validator_kind"),
                "validator_total_pnl": float(validator_result.get("total_pnl", 0.0)),
                "validator_trades": int(validator_result.get("trades", 0)),
                "sharpe_like": float(validator_result.get("sharpe_like", 0.0)),
                "fsr": float(validator_result.get("fsr", 0.0)),
                "max_drawdown": float(validator_result.get("max_drawdown", 0.0)),
                "dd_recovery_ticks": int(validator_result.get("dd_recovery_ticks", 0)),
            }
        )

    return row


def write_results_csv(rows: List[Dict[str, Any]], results_dir: Path) -> Path:
    results_dir.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    out_path = results_dir / f"strategy_runs_{ts}.csv"
    pd.DataFrame(rows).to_csv(out_path, index=False)
    return out_path
