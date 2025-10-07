
import numpy as np
import pandas as pd

class EWMAValidator:
    def __init__(self, alpha=0.05, z=2.5):
        self.alpha = alpha
        self.z = z
        self.mean = None
        self.var = 1.0
    def step(self, x):
        if self.mean is None:
            self.mean = x
            return False
        delta = x - self.mean
        self.mean += self.alpha * delta
        self.var = (1 - self.alpha) * (self.var + self.alpha * delta * delta)
        std = (self.var + 1e-12) ** 0.5
        z = abs((x - self.mean) / std)
        return z > self.z

class VolatilityValidator:
    """Trade only when recent *return* volatility is below a threshold."""
    def __init__(self, window=50, max_vol=0.01):
        self.window = window
        self.max_vol = max_vol
        self.buf = []
        self.prev = None
    def step(self, x):
        if self.prev is None:
            self.prev = x
            return False
        ret = (x - self.prev) / max(self.prev, 1e-9)
        self.prev = x
        self.buf.append(ret)
        if len(self.buf) > self.window:
            self.buf.pop(0)
        if len(self.buf) < 5:
            return False
        std = float(np.std(self.buf))
        return std < self.max_vol  # e.g., 0.003–0.02

class PersistenceValidator:
    """Require price to stay above a rolling mean by z for 'hold' ticks."""
    def __init__(self, hold=3, mean_alpha=0.05, z=0.2):
        self.hold = hold
        self.mean_alpha = mean_alpha
        self.z = z
        self.mean = None
        self.c = 0
    def step(self, x):
        if self.mean is None:
            self.mean = x
            return False
        delta = x - self.mean
        self.mean += self.mean_alpha * delta
        if delta > self.z:
            self.c += 1
        else:
            self.c = 0
        return self.c >= self.hold

class ImbalanceValidator:
    def __init__(self, thr=0.6):
        self.thr = thr
    def step(self, x):
        imb = 0.7 if (x % 2) > 1 else 0.4
        return imb > self.thr

def simulate(df, validator, latency_ticks=1, cost_bps=0.5, slip_bps=0.3, position=1.0):
    """Simple simulator:
    - If validator fires, enter after latency_ticks, exit 1 tick later in trade direction.
    - Apply round-trip transaction costs and slippage (bps on entry & exit).
    - position scales PnL and costs linearly.
    """
    price = df["price"].values
    trades = []
    pnl_series = []
    last_trade_idx = -9999
    bps_factor = (cost_bps + slip_bps) * 1e-4 * 2.0  # round-trip

    for i in range(len(price)):
        signal = validator.step(price[i])
        if signal and i - last_trade_idx > latency_ticks:
            j = min(i + latency_ticks, len(price)-1)
            direction = 1 if price[j] - price[i] >= 0 else -1
            k = min(j + 1, len(price)-1)
            gross = position * (price[k] - price[j]) * direction
            costs = position * price[j] * bps_factor
            trade_pnl = gross - costs
            trades.append({"i": i, "j": j, "k": k, "dir": direction, "pnl": float(trade_pnl)})
            pnl_series.append(trade_pnl)
            last_trade_idx = i

    pnl_series = np.array(pnl_series) if pnl_series else np.array([0.0])
    total_pnl = float(pnl_series.sum())
    fsr = float((pnl_series < 0).mean()) if len(pnl_series) > 0 else 0.0
    sharpe_like = float(pnl_series.mean() / (pnl_series.std()+1e-12)) if len(pnl_series)>1 else 0.0

    equity = np.cumsum(pnl_series)
    dd = 0.0; peak = 0.0; rec = 0; in_dd=False; start=0
    for idx, eq in enumerate(equity):
        if eq > peak:
            peak = eq; in_dd=False
        draw = peak - eq
        if draw > dd:
            dd = draw; in_dd=True; start = idx
        if in_dd and eq >= peak - 1e-12:
            rec = max(rec, idx - start); in_dd=False

    return {
        "total_pnl": total_pnl,
        "trades": len(trades),
        "fsr": fsr,
        "sharpe_like": sharpe_like,
        "dd_recovery_ticks": int(rec),
        "pnl_series": pnl_series.tolist(),
        "equity": equity.tolist() if len(pnl_series)>1 else [0.0],
        "trades_detail": trades
    }
