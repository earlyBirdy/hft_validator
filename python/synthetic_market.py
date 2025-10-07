import numpy as np
import pandas as pd

def gbm(n=5000, mu=0.00005, sigma=0.01, s0=100.0, dt=1.0):
    shocks = np.random.normal((mu - 0.5*sigma**2)*dt, sigma*np.sqrt(dt), size=n)
    log_price = np.log(s0) + np.cumsum(shocks)
    return np.exp(log_price)

def garch11(n=5000, omega=1e-6, alpha=0.05, beta=0.9, mu=0.0, s0=100.0):
    eps = np.zeros(n)
    var = np.zeros(n)
    var[0] = omega/(1.0 - alpha - beta)
    for t in range(1, n):
        eps[t-1] = np.sqrt(var[t-1]) * np.random.randn()
        var[t] = omega + alpha*eps[t-1]**2 + beta*var[t-1]
    eps[-1] = np.sqrt(var[-1]) * np.random.randn()
    ret = mu + eps
    price = s0 * np.exp(np.cumsum(ret))
    return price

def jump_diffusion(n=5000, mu=0.00003, sigma=0.008, lam=0.001, jump_mu=-0.02, jump_sigma=0.04, s0=100.0):
    dt = 1.0
    normals = np.random.normal((mu - 0.5*sigma**2)*dt, sigma*np.sqrt(dt), size=n)
    jumps = np.random.poisson(lam*dt, size=n) * np.random.normal(jump_mu, jump_sigma, size=n)
    log_price = np.log(s0) + np.cumsum(normals + jumps)
    return np.exp(log_price)

def labeled_scenarios(n=5000, s0=100.0):
    seg = n//3
    p1 = gbm(seg, mu=0.00004, sigma=0.006, s0=s0)
    p2 = garch11(seg, omega=1e-6, alpha=0.08, beta=0.88, s0=p1[-1])
    p3 = jump_diffusion(n-seg*2, lam=0.002, jump_mu=-0.03, s0=p2[-1])
    price = np.concatenate([p1, p2, p3])
    label = (["calm_trend"]*seg) + (["volatile"]*seg) + (["jumpy"]*(n-seg*2))
    ts = np.arange(n)
    df = pd.DataFrame({"t": ts, "price": price, "regime": label})
    return df
