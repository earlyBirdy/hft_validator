from dataclasses import dataclass
import json
from typing import Dict

@dataclass
class Metrics:
    pnl: float
    trades: int
    wins: int
    max_dd: float
    sharpe: float

    @staticmethod
    def from_cpp_json(s: str) -> "Metrics":
        obj = json.loads(s)
        return Metrics(
            pnl=float(obj["pnl"]),
            trades=int(obj["trades"]),
            wins=int(obj["wins"]),
            max_dd=float(obj["max_dd"]),
            sharpe=float(obj["sharpe"]),
        )

    def to_dict(self) -> Dict:
        return dict(pnl=self.pnl, trades=self.trades, wins=self.wins, max_dd=self.max_dd, sharpe=self.sharpe)
