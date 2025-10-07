
import os, json
import pandas as pd
import matplotlib.pyplot as plt
from synthetic_market import labeled_scenarios
from validator_sim import EWMAValidator, VolatilityValidator, PersistenceValidator, simulate
from agent_reasoner import decide, log_decision

def run_pipeline(
    n_ticks=3000,
    # validator params
    ewma_alpha=0.05, ewma_z=2.5,
    vol_window=50, vol_max=0.03,
    persist_hold=3, persist_thresh=0.0,
    # latency in ticks (coarse proxy): baseline vs agent
    baseline_latency=5, agent_latency=1,
    # output locations
    out_dir="../results", logs_path="../aws/reasoning_logs.jsonl"
):
    df = labeled_scenarios(n=n_ticks)
    regimes = df['regime'].unique().tolist()

    # Baseline (EWMA only) with higher latency
    base = simulate(df, EWMAValidator(ewma_alpha, ewma_z), latency_ticks=baseline_latency)

    # Agent: adaptive per regime with lower latency
    results = {}
    logs = []
    # reset logs
    os.makedirs(os.path.dirname(logs_path), exist_ok=True)
    open(logs_path, "w").close()

    for reg in regimes:
        sub = df[df['regime']==reg]
        dec = decide({"current_regime": reg})
        # override chosen validator params with provided knobs when applicable
        if dec["validator"] == "EWMA":
            res = simulate(sub, EWMAValidator(ewma_alpha, ewma_z), latency_ticks=agent_latency)
        elif dec["validator"] == "Volatility":
            res = simulate(sub, VolatilityValidator(vol_window, vol_max), latency_ticks=agent_latency)
        else:
            res = simulate(sub, PersistenceValidator(persist_hold, persist_thresh), latency_ticks=agent_latency)
        results[reg] = res
        logs.append(log_decision(dec, {"regime": reg}))

    import numpy as np
    agg = {
        "total_pnl": float(sum(r["total_pnl"] for r in results.values())),
        "trades": int(sum(r["trades"] for r in results.values())),
        "fsr": float(np.mean([r["fsr"] for r in results.values()])),
        "sharpe_like": float(np.mean([r["sharpe_like"] for r in results.values()])),
        "dd_recovery_ticks": int(np.mean([r["dd_recovery_ticks"] for r in results.values()])),
        "adaptive_switch_count": len(regimes)-1
    }

    os.makedirs(out_dir, exist_ok=True)

    # Metrics bar chart
    labels = ["FSR", "Sharpe-like", "DD Recovery"]
    base_vals = [base["fsr"], base["sharpe_like"], base["dd_recovery_ticks"]]
    agent_vals = [agg["fsr"], agg["sharpe_like"], agg["dd_recovery_ticks"]]

    plt.figure(figsize=(8,4))
    x = range(len(labels))
    plt.bar([i-0.15 for i in x], base_vals, width=0.3, label=f"Baseline (EWMA, {baseline_latency} ticks)")
    plt.bar([i+0.15 for i in x], agent_vals, width=0.3, label=f"Agent (Adaptive, {agent_latency} ticks)")
    plt.xticks(list(x), labels)
    plt.title("Baseline vs Agent — Key Metrics")
    plt.legend()
    metrics_img = os.path.join(out_dir, "metrics_compare.png")
    plt.tight_layout(); plt.savefig(metrics_img, dpi=140); plt.close()

    # Timeline of reasoning logs
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

    # CSV summary
    import csv
    summary_csv = os.path.join(out_dir, "summary.csv")
    with open(summary_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["metric","baseline","agent"])
        w.writerow(["total_pnl", base["total_pnl"], agg["total_pnl"]])
        w.writerow(["trades", base["trades"], agg["trades"]])
        w.writerow(["fsr", base["fsr"], agg["fsr"]])
        w.writerow(["sharpe_like", base["sharpe_like"], agg["sharpe_like"]])
        w.writerow(["dd_recovery_ticks", base["dd_recovery_ticks"], agg["dd_recovery_ticks"]])
        w.writerow(["adaptive_switch_count", 0, agg["adaptive_switch_count"]])

    return {
        "baseline": base,
        "agent": agg,
        "artifacts": {
            "metrics_img": metrics_img,
            "timeline_img": timeline_img,
            "summary_csv": summary_csv
        }
    }

if __name__ == "__main__":
    # default params
    run_pipeline()
    print("Saved artifacts to ../results")
