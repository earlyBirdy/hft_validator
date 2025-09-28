
from typing import List, Tuple, Dict
from .metrics import compute_metrics

def ewma_strategy(prices: List[Tuple[str,float]], alpha=0.05, threshold=2.5, window=50):
    metrics, _ = ewma_run(prices, alpha=alpha, threshold=threshold, window=window)
    return metrics

def persistence_strategy(prices: List[Tuple[str,float]], hold_period=10):
    metrics, _ = persistence_run(prices, hold_period=hold_period)
    return metrics

def ewma_run(prices: List[Tuple[str,float]], alpha=0.05, threshold=2.5, window=50):
    if len(prices)<window+2: 
        raise ValueError("Not enough data")
    p0=prices[0][1]; eq=[0.0]; ewma=p0; var=0.0; pos=0; trades=0; wins=0
    for i in range(1,len(prices)):
        px=prices[i][1]; prev=prices[i-1][1]; ret=px-prev
        ewma=alpha*px+(1-alpha)*ewma
        diff=px-ewma; var=(1-alpha)*(var+alpha*diff*diff); vol=(var if var>1e-12 else 1e-12)**0.5
        upper=ewma+threshold*vol; lower=ewma-threshold*vol
        new_pos=pos
        if px>upper: new_pos=+1
        elif px<lower: new_pos=-1
        if new_pos!=pos: 
            trades+=1
        if (pos==+1 and ret>0) or (pos==-1 and ret<0): 
            wins+=1
        pos=new_pos; eq.append(eq[-1]+pos*ret)
    M=compute_metrics(eq).__dict__; M["trades"]=trades; M["wins"]=wins
    return M, eq

def persistence_run(prices: List[Tuple[str,float]], hold_period=10):
    eq=[0.0]; pos=0; hold=0; trades=0; wins=0
    for i in range(1,len(prices)):
        px=prices[i][1]; prev=prices[i-1][1]; ret=px-prev
        if hold==0: 
            pos=1 if ret>0 else -1; trades+=1; hold=hold_period
        else: 
            hold-=1
        if (pos==+1 and ret>0) or (pos==-1 and ret<0): 
            wins+=1
        eq.append(eq[-1]+pos*ret)
    M=compute_metrics(eq).__dict__; M["trades"]=trades; M["wins"]=wins
    return M, eq

STRATEGIES = {
    "EWMA": ewma_strategy,
    "PERSIST": persistence_strategy,
}

def list_strategies() -> Dict[str, str]:
    return {
        "EWMA": "EWMA band breakout with volatility bands (params: alpha, threshold, window)",
        "PERSIST": "Directional persistence/hold strategy (params: hold_period)"
    }
