
from __future__ import annotations
import numpy as np
import pandas as pd

def _stochastic_k(close: np.ndarray, high: np.ndarray, low: np.ndarray, period: int) -> np.ndarray:
    k = np.zeros_like(close, dtype=float)
    for i in range(len(close)):
        s = max(0, i - period + 1)
        hh = np.max(high[s:i+1])
        ll = np.min(low[s:i+1])
        denom = (hh - ll) if (hh - ll) > 1e-12 else 1e-12
        k[i] = 100.0 * (close[i] - ll) / denom
    return k

def _sma(x: np.ndarray, n: int) -> np.ndarray:
    if n <= 1:
        return x.astype(float)
    out = np.zeros_like(x, dtype=float)
    csum = np.cumsum(np.insert(x.astype(float), 0, 0.0))
    for i in range(len(x)):
        s = max(0, i - n + 1)
        out[i] = (csum[i+1] - csum[s]) / (i - s + 1)
    return out

def compute_kd(df: pd.DataFrame, k_period=9, d_period=3, smooth=3) -> pd.DataFrame:
    close = df["price"].to_numpy(dtype=float)
    high = df.get("high", df["price"]).to_numpy(dtype=float)
    low = df.get("low", df["price"]).to_numpy(dtype=float)

    k_raw = _stochastic_k(close, high, low, k_period)
    k_s = _sma(k_raw, smooth)
    d = _sma(k_s, d_period)

    out = df.copy()
    out["K"] = k_s
    out["D"] = d
    return out

def generate_kd_signals(df_kd: pd.DataFrame, oversold=20, overbought=80) -> pd.DataFrame:
    df = df_kd.copy()
    K = df["K"].to_numpy()
    D = df["D"].to_numpy()

    bull = np.zeros(len(df), dtype=bool)
    bear = np.zeros(len(df), dtype=bool)
    for i in range(1, len(df)):
        bull[i] = (K[i-1] <= D[i-1]) and (K[i] > D[i])
        bear[i] = (K[i-1] >= D[i-1]) and (K[i] < D[i])

    df["bull_cross"] = bull
    df["bear_cross"] = bear
    df["long_zone"] = np.minimum(K, D) < oversold
    df["short_zone"] = np.maximum(K, D) > overbought
    df["long_signal"] = df["bull_cross"] & df["long_zone"]
    df["short_signal"] = df["bear_cross"] & df["short_zone"]
    return df
