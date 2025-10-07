
import os, sys, json
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

REPO = os.path.abspath(os.path.dirname(__file__))
PY_DIR = os.path.join(REPO, "python")
AWS_DIR = os.path.join(REPO, "aws")
RESULTS_DIR = os.path.join(REPO, "results")

if PY_DIR not in sys.path:
    sys.path.insert(0, PY_DIR)

import visualize_metrics as vm
import optimizer

st.set_page_config(page_title="AgentGuard Dashboard", layout="wide")
st.title("AgentGuard — Local Dashboard")
st.caption("Baseline vs Agent metrics, validator choices, and reasoning logs (local simulation)")

with st.sidebar:
    st.header("Controls")
    st.markdown("**Simulation**")
    n_ticks = st.slider("Ticks", min_value=600, max_value=12000, value=3000, step=200)

    st.markdown("---")
    st.markdown("**EWMA Params**")
    ewma_alpha = st.slider("EWMA α (alpha)", 0.001, 0.2, 0.05, 0.001)
    ewma_z = st.slider("Z-score threshold", 1.0, 5.0, 2.0, 0.1)

    st.markdown("**Volatility (returns) Params**")
    vol_window = st.slider("Vol window (ticks)", 10, 200, 50, 5)
    vol_max = st.slider("Max return vol (σ)", 0.001, 0.05, 0.01, 0.001)

    st.markdown("**Persistence (rolling mean) Params**")
    persist_hold = st.slider("Hold ticks", 1, 20, 3, 1)
    persist_mean_alpha = st.slider("Rolling mean α", 0.001, 0.2, 0.05, 0.001)
    persist_z = st.slider("Above-mean threshold", 0.0, 1.0, 0.2, 0.01)

    st.markdown("---")
    st.markdown("**Latency (proxy, ticks)**")
    baseline_latency = st.slider("Baseline latency", 1, 20, 5, 1)
    agent_latency = st.slider("Agent latency", 1, 10, 1, 1)

    st.markdown("---")
    st.markdown("**Costs & Positions**")
    cost_bps = st.slider("Transaction cost (bps)", 0.0, 5.0, 0.8, 0.1)
    slip_bps = st.slider("Slippage (bps)", 0.0, 5.0, 0.5, 0.1)
    pos_calm = st.slider("Position — Calm", 0.1, 2.0, 1.0, 0.05)
    pos_volatile = st.slider("Position — Volatile", 0.1, 2.0, 0.6, 0.05)
    pos_jumpy = st.slider("Position — Jumpy", 0.1, 2.0, 0.4, 0.05)

    rerun = st.button("Run Simulation Pipeline")
    apply_best = st.button("Apply Best Params (from best_params.json)")

    tune = st.button("Auto-tune (local random search)")

if rerun:
    res = vm.run_pipeline(
        n_ticks=n_ticks,
        ewma_alpha=ewma_alpha, ewma_z=ewma_z,
        vol_window=vol_window, vol_max=vol_max,
        persist_hold=persist_hold, persist_mean_alpha=persist_mean_alpha, persist_z=persist_z,
        baseline_latency=baseline_latency, agent_latency=agent_latency,
        cost_bps=cost_bps, slip_bps=slip_bps,
        pos_calm=pos_calm, pos_volatile=pos_volatile, pos_jumpy=pos_jumpy,
        out_dir=RESULTS_DIR, logs_path=os.path.join(AWS_DIR, "reasoning_logs.jsonl"),
        generate_artifacts=True
    )
    st.success("Pipeline run complete. Results refreshed.")

if tune:
    st.info("Running local random search (25 trials)...")
    best = optimizer.random_search(iters=25, seed=42, out_json=os.path.join(RESULTS_DIR, "best_params.json"))
    if best:
        st.success(f"Best score: {best['score']:.4f}")
        st.json(best)
    else:
        st.error("Tuning failed")

summary_path = os.path.join(RESULTS_DIR, "summary.csv")
col1, col2 = st.columns(2)
if os.path.exists(summary_path):
    df = pd.read_csv(summary_path)
    with col1:
        st.subheader("Metrics Summary")
        st.dataframe(df, use_container_width=True)
else:
    st.info("No summary.csv found. Click 'Run Simulation Pipeline' to generate.")

metrics_img = os.path.join(RESULTS_DIR, "metrics_compare.png")
timeline_img = os.path.join(RESULTS_DIR, "agent_decisions_timeline.png")
with col2:
    if os.path.exists(metrics_img):
        st.subheader("Baseline vs Agent — Key Metrics (with costs & scaling)")
        st.image(metrics_img, use_column_width=True)
    if os.path.exists(timeline_img):
        st.subheader("Agent Decisions Timeline")
        st.image(timeline_img, use_column_width=True)

st.subheader("Reasoning Logs")
logs_path = os.path.join(AWS_DIR, "reasoning_logs.jsonl")
if os.path.exists(logs_path) and os.path.getsize(logs_path) > 0:
    rows = []
    with open(logs_path) as f:
        for line in f:
            try:
                rows.append(json.loads(line.strip()))
            except Exception:
                pass
    if rows:
        df_logs = pd.DataFrame(rows)
        st.dataframe(df_logs, use_container_width=True, height=240)
        counts = df_logs["decision"].value_counts().rename_axis("validator").reset_index(name="count")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        ax.bar(counts["validator"], counts["count"])
        ax.set_title("Validator Decision Counts")
        st.pyplot(fig)
else:
    st.info("No reasoning logs found. Run the pipeline to generate logs.")

st.markdown("---")
st.subheader("Downloads")
colA, colB, colC = st.columns(3)
if os.path.exists(summary_path):
    with open(summary_path, "rb") as f:
        colA.download_button("Download summary.csv", f, file_name="summary.csv")
if os.path.exists(metrics_img):
    with open(metrics_img, "rb") as f:
        colB.download_button("Download metrics_compare.png", f, file_name="metrics_compare.png")
if os.path.exists(timeline_img):
    with open(timeline_img, "rb") as f:
        colC.download_button("Download agent_decisions_timeline.png", f, file_name="agent_decisions_timeline.png")

st.divider()
st.caption("Tune parameters on the left, then rerun to refresh metrics. Use Auto-tune for a quick local search.")

# Equity curves image
eq_img = os.path.join(RESULTS_DIR, "equity_curves.png")
if os.path.exists(eq_img):
    st.subheader("Equity Curves — Baseline vs Agent")
    st.image(eq_img, use_column_width=True)

# Per-regime metrics table & download
per_regime_csv = os.path.join(RESULTS_DIR, "per_regime_metrics.csv")
if os.path.exists(per_regime_csv):
    st.subheader("Per-Regime Metrics")
    pr_df = pd.read_csv(per_regime_csv)
    st.dataframe(pr_df, use_container_width=True)
    st.download_button("Download per_regime_metrics.csv", data=open(per_regime_csv,"rb"), file_name="per_regime_metrics.csv")

