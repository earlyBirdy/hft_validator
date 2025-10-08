
import numpy as np
import pandas as pd

def _gbm(n, s0=100.0, mu=0.0, sigma=0.01):
    dt = 1.0
    returns = np.random.normal((mu - 0.5*sigma**2)*dt, sigma*np.sqrt(dt), size=n)
    price = s0 * np.exp(np.cumsum(returns))
    return price

def labeled_scenarios(n=3000, seed=123):
    np.random.seed(seed)
    # split into 3 regimes: calm_trend, volatile, jumpy
    n1 = n//3
    n2 = n//3
    n3 = n - n1 - n2

    # calm trending up (low vol)
    p1 = _gbm(n1, s0=100.0, mu=0.002, sigma=0.005)
    # volatile sideways (higher vol)
    p2 = _gbm(n2, s0=float(p1[-1]), mu=0.0, sigma=0.02)
    # jumpy (vol clusters + jumps)
    base = _gbm(n3, s0=float(p2[-1]), mu=0.0, sigma=0.015)
    jumps = np.random.choice([0.0, 0.02, -0.02, 0.04, -0.04], size=n3, p=[0.94,0.02,0.02,0.01,0.01])
    base *= np.cumprod(1.0 + jumps)

    price = np.concatenate([p1, p2, base])
    regime = (["calm_trend"]*n1) + (["volatile"]*n2) + (["jumpy"]*n3)
    df = pd.DataFrame({"price": price, "regime": regime})
    return df
