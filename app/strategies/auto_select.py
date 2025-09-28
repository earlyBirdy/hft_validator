from typing import List, Tuple, Dict
from ..backtester import ewma_strategy, persistence_strategy

def _features(prices: List[Tuple[str,float]])->Dict:
    import statistics
    rets=[prices[i][1]-prices[i-1][1] for i in range(1,len(prices))]
    vol=statistics.pstdev(rets) if len(rets)>1 else 0.0
    trend=(prices[-1][1]-prices[0][1])/(abs(prices[0][1])+1e-9)
    return {"vol":vol,"trend":trend}

def smart_choose_and_run(prices: List[Tuple[str,float]])->Dict:
    feats=_features(prices); candidates=[]
    # Favor EWMA on trendier & moderate-vol regimes; wider grid
    if abs(feats["trend"])>0.008 and feats["vol"]<0.6:
        grid=[(0.02,1.8,90),(0.03,2.0,80),(0.05,2.5,50),(0.08,3.0,30),(0.10,3.2,25)]
        for a,t,w in grid:
            m=ewma_strategy(prices, alpha=a, threshold=t, window=w)
            candidates.append(("EWMA", {"alpha":a,"threshold":t,"window":w}, m))
    else:
        for h in [5,8,12,16]:
            m=persistence_strategy(prices, hold_period=h)
            candidates.append(("PERSIST", {"hold_period":h}, m))
    best=max(candidates, key=lambda x: (x[2]["sharpe"], x[2]["pnl"]))
    return {"strategy":best[0],"params":best[1],"metrics":best[2],"features":feats,"candidates":candidates}
