import os, json, argparse, io, base64
from datetime import datetime, UTC
from app.data import load_prices_csv
from app.backtester import ewma_strategy, persistence_strategy, ewma_run, persistence_run, list_strategies
from app.strategies.auto_select import smart_choose_and_run

def select_agent():
    impl=os.environ.get("AGENT_IMPL","local").lower()
    if impl=="bedrock":
        from app.agent.bedrock import decide
    else:
        from app.agent.local import decide
    return decide

def run_baseline(prices):
    return {"strategy":"EWMA","params":{"alpha":0.05,"threshold":2.5,"window":50},
            "metrics": ewma_strategy(prices, alpha=0.05, threshold=2.5, window=50)}

def generate_report_html(path, prices, baseline, final):
    # Recompute equity curves and detect overlap
    from math import isclose
    _, eq_base = ewma_run(prices, **baseline["params"]) if baseline["strategy"]=="EWMA" else persistence_run(prices, **baseline["params"])
    if final["strategy"]=="EWMA":
        _, eq_final = ewma_run(prices, **final["params"])
    else:
        _, eq_final = persistence_run(prices, **final["params"])

    same_len = len(eq_base) == len(eq_final)
    identical = same_len and all(isclose(a, b, rel_tol=1e-12, abs_tol=1e-12) for a, b in zip(eq_base, eq_final))

    import matplotlib.pyplot as plt
    plt.figure()
    # Keep default colors, but visually distinguish
    plt.plot(eq_base, label="Baseline", linestyle="-")
    plt.plot(eq_final, label="Final" + (" (identical)" if identical else ""), linestyle="--" if identical else "-", alpha=0.85)
    plt.legend()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    plt.close()
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")

    def row(name, m):
        return f"<tr><td>{name}</td><td>{m['pnl']:.4f}</td><td>{m['trades']}</td><td>{m['wins']}</td><td>{m['max_dd']:.4f}</td><td>{m['sharpe']:.4f}</td></tr>"

    identical_note = "<p><em>Note: Baseline and Final equity curves are identical for this run.</em></p>" if identical else ""

    html = f"""<!doctype html><html><head><meta charset='utf-8'><title>HFT Validator Report</title>
<style>body{{font-family:Arial;margin:20px}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #ddd;padding:8px;text-align:right}}th{{text-align:center}}td:first-child,th:first-child{{text-align:left}}</style>
</head><body>
<h1>HFT Validator Report</h1>
<p><small>Generated: {datetime.now(UTC).isoformat()}</small></p>
{identical_note}
<h2>Equity (Baseline vs Final)</h2>
<img alt="equity" src="data:image/png;base64,{b64}">
<h2>Metrics</h2>
<table><thead><tr><th>Run</th><th>PNL</th><th>Trades</th><th>Wins</th><th>Max DD</th><th>Sharpe</th></tr></thead>
<tbody>
{row("Baseline", baseline["metrics"])}
{row("Final", final["metrics"])}
</tbody></table>
<h2>Params</h2>
<table><thead><tr><th>Run</th><th>Strategy</th><th>Params</th></tr></thead><tbody>
<tr><td>Baseline</td><td>{baseline["strategy"]}</td><td><pre>{json.dumps(baseline["params"], indent=2)}</pre></td></tr>
<tr><td>Final</td><td>{final["strategy"]}</td><td><pre>{json.dumps(final["params"], indent=2)}</pre></td></tr>
</tbody></table>
</body></html>"""
    with open(path, "w") as f:
        f.write(html)

def main():
    ap = argparse.ArgumentParser(description="HFT Validator CLI")
    ap.add_argument("--list-strategies", action="store_true", help="List strategies/validators and exit.")
    ap.add_argument("--report", metavar="HTML_PATH", help="Write an HTML report (equity + metrics).")
    args = ap.parse_args()

    if args.list_strategies:
        print(json.dumps(list_strategies(), indent=2))
        return

    data_path=os.environ.get("DATA_PATH","data/sample_prices.csv")
    prices=load_prices_csv(data_path)
    baseline=run_baseline(prices)

    decide=select_agent()
    hint=decide({"timestamp": datetime.now(UTC).isoformat(), "baseline": baseline["metrics"]})
    chosen=smart_choose_and_run(prices)

    final_params=dict(chosen["params"])
    if chosen["strategy"]=="EWMA" and hint.get("hint_strategy")=="EWMA":
        hp=hint.get("hint_params",{})
        final_params["alpha"]=float(hp.get("alpha", final_params["alpha"]))
        final_params["threshold"]=float(hp.get("threshold", final_params["threshold"]))
        final_params["window"]=int(hp.get("window", final_params["window"]))
        final_metrics=ewma_strategy(prices, **final_params)
    elif chosen["strategy"]=="PERSIST" and hint.get("hint_strategy")=="PERSIST":
        hp=hint.get("hint_params",{})
        final_params["hold_period"]=int(hp.get("hold_period", final_params["hold_period"]))
        final_metrics=persistence_strategy(prices, **final_params)
    else:
        final_metrics=chosen["metrics"]

    result={"baseline":baseline,"smart":chosen,"agent_hint":hint,
            "final":{"strategy":chosen["strategy"],"params":final_params,"metrics":final_metrics},
            "improvement_sharpe_over_baseline": final_metrics["sharpe"]-baseline["metrics"]["sharpe"]}

    # Safeguard: require improvement (default ON). Disable with REQUIRE_IMPROVEMENT=0
    if os.environ.get("REQUIRE_IMPROVEMENT","1") == "1" and result["improvement_sharpe_over_baseline"] < 0:
        result["note"] = "Final Sharpe < baseline — falling back to baseline due to REQUIRE_IMPROVEMENT=1."
        result["final"] = result["baseline"]
        result["improvement_sharpe_over_baseline"] = 0.0

    if args.report:
        generate_report_html(args.report, prices, baseline, result["final"])

    print(json.dumps(result, indent=2))

if __name__=="__main__":
    main()
