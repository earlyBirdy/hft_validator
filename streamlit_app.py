
import os, sys, json
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "."))
PY_DIR = os.path.join(REPO, "python")
AWS_DIR = os.path.join(REPO, "aws")
RESULTS_DIR = os.path.join(REPO, "results")

if PY_DIR not in sys.path:
    sys.path.insert(0, PY_DIR)

import visualize_metrics as vm

st.set_page_config(page_title="AgentGuard Dashboard", layout="wide")
st.title("AgentGuard — Local Dashboard")
st.caption("Baseline vs Agent metrics, validator choices, and reasoning logs (local simulation)")

with st.sidebar:
    st.header("Controls")
    st.markdown("**Simulation**")
    n_ticks = st.slider("Ticks", min_value=600, max_value=10000, value=3000, step=200)

    st.markdown("---")
    st.markdown("**EWMA Params**")
    ewma_alpha = st.slider("EWMA α (alpha)", 0.001, 0.2, 0.05, 0.001)
    ewma_z = st.slider("Z-score threshold", 1.0, 5.0, 2.5, 0.1)

    st.markdown("**Volatility Params**")
    vol_window = st.slider("Vol window (ticks)", 10, 200, 50, 5)
    vol_max = st.slider("Max volatility", 0.005, 0.2, 0.03, 0.001)

    st.markdown("**Persistence Params**")
    persist_hold = st.slider("Hold ticks", 1, 20, 3, 1)
    persist_thresh = st.slider("Threshold offset", -2.0, 2.0, 0.0, 0.1)

    st.markdown("---")
    st.markdown("**Latency (proxy, ticks)**")
    baseline_latency = st.slider("Baseline latency", 1, 20, 5, 1)
    agent_latency = st.slider("Agent latency", 1, 10, 1, 1)

    rerun = st.button("Run Simulation Pipeline")

if rerun:
    res = vm.run_pipeline(
        n_ticks=n_ticks,
        ewma_alpha=ewma_alpha, ewma_z=ewma_z,
        vol_window=vol_window, vol_max=vol_max,
        persist_hold=persist_hold, persist_thresh=persist_thresh,
        baseline_latency=baseline_latency, agent_latency=agent_latency,
        out_dir=RESULTS_DIR, logs_path=os.path.join(AWS_DIR, "reasoning_logs.jsonl")
    )
    st.success("Pipeline run complete. Results refreshed.")

# Load and show the metrics summary if present
summary_path = os.path.join(RESULTS_DIR, "summary.csv")
col1, col2 = st.columns(2)
if os.path.exists(summary_path):
    df = pd.read_csv(summary_path)
    with col1:
        st.subheader("Metrics Summary")
        st.dataframe(df, use_container_width=True)
else:
    st.info("No summary.csv found. Click 'Run Simulation Pipeline' to generate.")

# Images
metrics_img = os.path.join(RESULTS_DIR, "metrics_compare.png")
timeline_img = os.path.join(RESULTS_DIR, "agent_decisions_timeline.png")
with col2:
    if os.path.exists(metrics_img):
        st.subheader("Baseline vs Agent — Key Metrics")
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
        # Validator decision counts
        counts = df_logs["decision"].value_counts().rename_axis("validator").reset_index(name="count")
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
st.caption("Tune parameters on the left, then rerun to refresh metrics. Download artifacts above for your submission.")
