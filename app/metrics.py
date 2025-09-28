from dataclasses import dataclass
from typing import List
@dataclass
class Metrics:
    pnl: float; trades:int; wins:int; max_dd:float; sharpe:float

def compute_metrics(eq: List[float]):
    import math
    if not eq: return Metrics(0,0,0,0,0)
    pnl=eq[-1]-eq[0]; peak=eq[0]; max_dd=0; rets=[]
    for i in range(1,len(eq)):
        x=eq[i]; r=eq[i]-eq[i-1]; rets.append(r); peak=max(peak,x); max_dd=max(max_dd, peak-x)
    m=sum(rets)/len(rets) if rets else 0
    v=sum((r-m)**2 for r in rets)/(len(rets)-1) if len(rets)>1 else 0
    sharpe=(len(rets)**0.5)*(m/(v**0.5)) if v>0 else 0
    return Metrics(pnl,0,0,max_dd,sharpe)
