
import os, json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from synthetic_market import labeled_scenarios
from validator_sim import EWMAValidator, VolatilityValidator, PersistenceValidator, ConfirmWrapper, simulate
from agent_reasoner import decide, log_decision

def _metrics_from_result(res):
    return {
        "total_pnl": float(res["total_pnl"]),
        "trades": int(res["trades"]),
        "fsr": float(res["fsr"]),
        "sharpe_like": float(res["sharpe_like"]),
        "dd_recovery_ticks": int(res["dd_recovery_ticks"]),
    }

def run_pipeline(
    n_ticks=3000,
    ewma_alpha=0.05, ewma_z=2.6,
    vol_window=60, vol_max=0.009,
    persist_hold=4, persist_mean_alpha=0.05, persist_z=0.28,
    baseline_latency=5, agent_latency=2,
    cost_bps=0.8, slip_bps=0.5,
    pos_calm=0.8, pos_volatile=0.45, pos_jumpy=0.35,
    min_interval_ticks=7, max_trades_per_100=12, confirm=2,
    out_dir="../results", logs_path="../aws/reasoning_logs.jsonl",
    generate_artifacts=True
):
    out_dir = os.path.abspath(out_dir)
    logs_path = os.path.abspath(logs_path)
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(os.path.dirname(logs_path), exist_ok=True)
    open(logs_path, "w").close()

    df = labeled_scenarios(n=n_ticks)
    regimes = df['regime'].unique().tolist()

    z_enter = ewma_z
    z_exit = max(ewma_z - 0.6, 1.2)

    base_res = simulate(
        df, ConfirmWrapper(EWMAValidator(ewma_alpha, z_enter, z_exit), confirm=confirm),
        latency_ticks=baseline_latency, cost_bps=cost_bps, slip_bps=slip_bps, position=1.0,
        min_interval_ticks=min_interval_ticks, max_trades_per_100=max_trades_per_100
    )
    base_equity = np.array(base_res.get("equity", [0.0]), dtype=float)

    per_regime = []
    agent_equity_parts = []
    for reg in regimes:
        sub = df[df['regime']==reg]
        dec = decide({"current_regime": reg})
        if reg == "calm_trend":
            pos = pos_calm
        elif reg == "volatile":
            pos = pos_volatile
        else:
            pos = pos_jumpy

        if dec["validator"] == "EWMA":
            v = ConfirmWrapper(EWMAValidator(ewma_alpha, z_enter, z_exit), confirm=confirm)
        elif dec["validator"] == "Volatility":
            v = ConfirmWrapper(VolatilityValidator(vol_window, vol_max), confirm=confirm)
        else:
            v = ConfirmWrapper(PersistenceValidator(persist_hold, persist_mean_alpha, persist_z), confirm=confirm)

        res = simulate(
            sub, v, latency_ticks=agent_latency, cost_bps=cost_bps, slip_bps=slip_bps, position=pos,
            min_interval_ticks=min_interval_ticks, max_trades_per_100=max_trades_per_100
        )

        log_decision(dec, {"regime": reg}, logs_path)
        met = _metrics_from_result(res)
        met["regime"] = reg
        per_regime.append(met)
        agent_equity_parts.append(np.array(res.get("equity", [0.0]), dtype=float))

    agent_equity = []
    offset = 0.0
    for seg in agent_equity_parts:
        if len(seg) == 0:
            continue
        seg_adj = seg + offset
        offset = seg_adj[-1]
        agent_equity.extend(seg_adj.tolist())
    agent_equity = np.array(agent_equity, dtype=float)

    agg = {
        "total_pnl": float(sum(m["total_pnl"] for m in per_regime)),
        "trades": int(sum(m["trades"] for m in per_regime)),
        "fsr": float(np.mean([m["fsr"] for m in per_regime])) if per_regime else 0.0,
        "sharpe_like": float(np.mean([m["sharpe_like"] for m in per_regime])) if per_regime else 0.0,
        "dd_recovery_ticks": int(np.mean([m["dd_recovery_ticks"] for m in per_regime])) if per_regime else 0,
        "adaptive_switch_count": max(len(per_regime)-1, 0)
    }

    artifacts = {}
    per_regime_csv = os.path.join(out_dir, "per_regime_metrics.csv")
    pd.DataFrame(per_regime)[["regime","total_pnl","trades","fsr","sharpe_like","dd_recovery_ticks"]].to_csv(per_regime_csv, index=False)
    artifacts["per_regime_csv"] = per_regime_csv

    summary_csv = os.path.join(out_dir, "summary.csv")
    with open(summary_csv, "w") as f:
        f.write("metric,baseline,agent\n")
        f.write(f"total_pnl,{base_res['total_pnl']},{agg['total_pnl']}\n")
        f.write(f"trades,{base_res['trades']},{agg['trades']}\n")
        f.write(f"fsr,{base_res['fsr']},{agg['fsr']}\n")
        f.write(f"sharpe_like,{base_res['sharpe_like']},{agg['sharpe_like']}\n")
        f.write(f"dd_recovery_ticks,{base_res['dd_recovery_ticks']},{agg['dd_recovery_ticks']}\n")
        f.write(f"adaptive_switch_count,0,{agg['adaptive_switch_count']}\n")
    artifacts["summary_csv"] = summary_csv

    if generate_artifacts:
        labels = ["FSR", "Sharpe-like", "DD Recovery"]
        base_vals = [base_res["fsr"], base_res["sharpe_like"], base_res["dd_recovery_ticks"]]
        agent_vals = [agg["fsr"], agg["sharpe_like"], agg["dd_recovery_ticks"]]

        plt.figure(figsize=(8,4))
        x = range(len(labels))
        plt.bar([i-0.15 for i in x], base_vals, width=0.3, label=f"Baseline (EWMA, {baseline_latency} ticks)")
        plt.bar([i+0.15 for i in x], agent_vals, width=0.3, label=f"Agent (Adaptive, {agent_latency} ticks)")
        plt.xticks(list(x), labels)
        plt.title("Baseline vs Agent — Key Metrics (gated & confirmed)")
        plt.legend()
        metrics_img = os.path.join(out_dir, "metrics_compare.png")
        plt.tight_layout(); plt.savefig(metrics_img, dpi=140); plt.close()
        artifacts["metrics_img"] = metrics_img

        plt.figure(figsize=(9,4))
        if base_vals is not None:
            plt.plot(np.array(base_res.get("equity", [0.0]), dtype=float), label="Baseline equity")
        plt.plot(agent_equity, label="Agent equity")
        plt.title("Cumulative PnL (Equity Curves) — Baseline vs Agent")
        plt.xlabel("Trade index")
        plt.ylabel("Cumulative PnL")
        plt.legend()
        eq_img = os.path.join(out_dir, "equity_curves.png")
        plt.tight_layout(); plt.savefig(eq_img, dpi=140); plt.close()
        artifacts["equity_img"] = eq_img

        with open(logs_path) as f:
            rows = [json.loads(line) for line in f]
        ylabels = [r["decision"] for r in rows]
        t = list(range(len(rows)))
        plt.figure(figsize=(8,2.8))
        plt.plot(t, list(range(1, len(rows)+1)), marker="o")
        plt.yticks(list(range(1, len(rows)+1)), ylabels)
        plt.xlabel("Decision step")
        plt.title("Agent Decisions Over Time")
        timeline_img = os.path.join(out_dir, "agent_decisions_timeline.png")
        plt.tight_layout(); plt.savefig(timeline_img, dpi=140); plt.close()
        artifacts["timeline_img"] = timeline_img

    return {
        "baseline": _metrics_from_result(base_res) | {"equity": base_res.get("equity", [0.0])},
        "agent": agg | {"equity": agent_equity.tolist()},
        "artifacts": artifacts
    }

if __name__ == "__main__":
    run_pipeline()
    print("Artifacts saved")
