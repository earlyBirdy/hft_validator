from __future__ import annotations
from typing import Dict, Any
import numpy as np
import pandas as pd

from config_loader import StrategySpec, get_exec_params
from kd_strategy import compute_kd, generate_kd_signals

def run(spec: StrategySpec, df: pd.DataFrame) -> Dict[str, Any]:
    params = get_exec_params(spec)
    kd = params["kd"]
    thr = params["thresholds"]
    max_pos = params["position"]["max_position"]

    df_kd = compute_kd(df, k_period=kd["k_period"], d_period=kd["d_period"], smooth=kd["smooth"])
    sig = generate_kd_signals(df_kd, oversold=thr["oversold"], overbought=thr["overbought"])

    pos = 0
    pnl = 0.0
    trades = 0
    price = sig["price"].to_numpy(dtype=float)

    for i in range(1, len(sig)):
        long_sig = bool(sig["long_signal"].iloc[i])
        short_sig = bool(sig["short_signal"].iloc[i])

        if long_sig:
            if pos < 0:
                pos = 0
            if pos < max_pos:
                pos += 1
                trades += 1
        elif short_sig:
            if pos > 0:
                pos = 0
            if pos > -max_pos:
                pos -= 1
                trades += 1

        pnl += pos * (price[i] - price[i-1])

    return {
        "strategy_id": spec.id,
        "strategy_name": spec.name,
        "strategy_type": spec.type,
        "total_pnl": float(pnl),
        "trades": int(trades),
    }
