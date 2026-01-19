import os, sys, json, time, importlib, traceback
from typing import Dict, Any, Callable, List, Tuple
import pathlib
import streamlit as st

# Ensure repo root is importable even if Streamlit runs from another CWD
ROOT = pathlib.Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Make ./python utilities importable (they use local imports like `from config_loader ...`).
PY_DIR = ROOT / "python"
if str(PY_DIR) not in sys.path:
    sys.path.insert(0, str(PY_DIR))

from web_bridge import (
    list_strategy_configs,
    read_price_df_from_upload,
    make_synthetic_df,
    get_strategy_catalog,
    run_strategy_on_df,
    run_validator_sim,
    make_unified_row,
    write_results_csv,
)
from config_loader import load_config

st.set_page_config(page_title="HFT Validator - Agent Console", page_icon="🤖", layout="wide")
st.title("🤖 HFT Validator — Agent Console")
st.caption("Select a validator engine, toggle Local/AWS mode, provide metrics, and run a decision.")

_CANDIDATES: List[Tuple[str, str, str]] = [
    ("Bedrock LLM", "python.agent_bedrock", "run_agent"),
    ("Local Rule-Based", "agents.local_agent.agent", "decide"),
    ("Python Validator", "python.agent_validator", "run_agent"),
    ("App Bedrock Wrapper", "app.agent.bedrock", "run_agent"),
    ("Bedrock Wrapper (shim)", "agents.bedrock_agent.agent", "decide"),
]

def discover_validators():
    found = {}
    diag = []
    for label, modname, attr in _CANDIDATES:
        try:
            mod = importlib.import_module(modname)
            fn = getattr(mod, attr, None)
            if callable(fn):
                found[label] = fn
                diag.append((label, modname, attr, "OK"))
            else:
                diag.append((label, modname, attr, f"Missing attr: {attr}"))
        except Exception as e:
            diag.append((label, modname, attr, f"Import error: {e}"))
    return found, diag

@st.cache_resource(show_spinner=False)
def get_registry():
    return discover_validators()

REGISTRY, DIAG = get_registry()
AVAILABLE = list(REGISTRY.keys())

st.sidebar.header("⚙️ Settings")
mode = st.sidebar.radio("Mode", ["Local (Dry-Run)", "AWS (Bedrock)"], index=0)

default_region = os.environ.get("AWS_REGION", "us-east-1")
default_model  = os.environ.get("BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0")
region = st.sidebar.text_input("AWS Region", value=default_region)
model_id = st.sidebar.text_input("Bedrock Model ID", value=default_model)

st.sidebar.write("---")
st.sidebar.subheader("🧰 Validator Engine")

if not AVAILABLE:
    st.sidebar.error("No validators discovered. See diagnostics below.")
else:
    default_label = "Bedrock LLM" if (mode.startswith("AWS") and "Bedrock LLM" in AVAILABLE) else AVAILABLE[0]
    validator_choice = st.sidebar.selectbox("Choose validator", AVAILABLE, index=AVAILABLE.index(default_label))
    st.sidebar.caption("**Discovered:**")
    for lbl in AVAILABLE:
        st.sidebar.caption(f"• {lbl}")

st.sidebar.write("---")
with st.sidebar.expander("🔎 Discovery Diagnostics", expanded=False):
    st.text(f"PYTHONPATH[0]: {sys.path[0]}")
    for label, mod, attr, msg in DIAG:
        st.write(f"- {label} → `{mod}.{attr}`: {msg}")

tab_decision, tab_strategy, tab_validator = st.tabs(
    ["🧠 Decision", "🧩 Strategy Runner", "✅ Validator Sim & Compare"]
)

def set_mode_env(mode: str, region: str, model_id: str):
    if mode.startswith("Local"):
        os.environ["HFT_AGENT_DRYRUN"] = "1"
    else:
        if "HFT_AGENT_DRYRUN" in os.environ:
            del os.environ["HFT_AGENT_DRYRUN"]
        os.environ["AWS_REGION"] = region.strip()
        os.environ["BEDROCK_MODEL_ID"] = model_id.strip()

def as_json(s: str) -> Dict[str, Any]:
    try:
        return json.loads(s)
    except Exception as e:
        raise ValueError(f"Invalid JSON for metrics: {e}")


with tab_decision:
    st.subheader("📊 Input Metrics (JSON)")
    example = {"sharpe_like": 0.8, "max_drawdown": 0.05, "trades": 120}
    if st.button("Load Example Metrics"):
        st.session_state["metrics_text"] = json.dumps(example, indent=2)

    metrics_text = st.text_area(
        "Provide recent trading metrics as JSON",
        value=st.session_state.get("metrics_text", json.dumps(example, indent=2)),
        height=200,
    )

    col1, col2 = st.columns([1, 1])
    run_clicked = col1.button("🚀 Run Decision")
    clear_clicked = col2.button("🧹 Clear Output")

    if clear_clicked:
        for k in ["last_output_text", "last_error", "last_engine"]:
            st.session_state.pop(k, None)
        st.rerun()

    st.write("---")
    st.subheader("🧠 Decision Output")
    if AVAILABLE:
        st.info(f"Active engine: **{validator_choice}** | Mode: **{mode}**")

    if run_clicked and AVAILABLE:
        try:
            set_mode_env(mode, region, model_id)
            agent_fn = REGISTRY[validator_choice]
            metrics = as_json(metrics_text)
            metrics["_ui_validator_choice"] = validator_choice
            metrics["_ui_mode"] = "dryrun" if mode.startswith("Local") else "aws"

            with st.spinner(f"Running {validator_choice}..."):
                start = time.time()
                decision = agent_fn(metrics)
                elapsed = time.time() - start

            st.success(f"Completed in {elapsed:.2f}s")
            st.code(json.dumps(decision, indent=2), language="json")

            st.write("**Validator (reported):**", decision.get("validator", "—"))
            st.write("**Params:**")
            st.json(decision.get("params", {}))
            with st.expander("Reasoning"):
                st.write(decision.get("reason", "—"))

            st.session_state["last_output_text"] = json.dumps(decision, indent=2)
            st.session_state["last_engine"] = validator_choice

        except Exception as e:
            st.error(f"Run failed: {e}")
            st.exception(e)

    if "last_output_text" in st.session_state and not run_clicked:
        st.code(st.session_state["last_output_text"], language="json")
        if "last_engine" in st.session_state:
            st.caption(f"Last run engine: {st.session_state['last_engine']}")


with tab_strategy:
    st.subheader("🧩 Strategy Runner")
    st.caption("Select a data source, pick one or more strategy configs, run them, and export a unified results CSV.")

    # Data source
    data_source = st.radio("Data Source", ["Synthetic", "CSV Upload"], horizontal=True)

    df = None
    n_ticks = 3000
    if data_source == "Synthetic":
        n_ticks = int(st.number_input("n_ticks", min_value=200, max_value=200000, value=3000, step=100))
        seed = int(st.number_input("seed", min_value=0, max_value=10_000_000, value=123, step=1))
        df = make_synthetic_df(n_ticks=n_ticks, seed=seed)
        st.success(f"Synthetic series ready: {len(df)} ticks")
    else:
        up = st.file_uploader("Upload CSV", type=["csv"])
        if up is not None:
            df = read_price_df_from_upload(up.getvalue(), up.name)
            n_ticks = len(df)
            st.success(f"CSV series loaded: {len(df)} ticks")

    # Strategy catalog
    st.write("---")
    st.subheader("Discovered strategy types")
    st.json(get_strategy_catalog())

    strategies_dir = ROOT / "strategies"
    configs = list_strategy_configs(strategies_dir)
    if not configs:
        st.warning("No strategy configs found in ./strategies")
    else:
        config_labels = [str(p.relative_to(ROOT)) for p in configs]
        selected = st.multiselect("Select strategy configs", options=config_labels, default=config_labels[:1])

        run_all = st.button("▶️ Run selected configs")
        if run_all and df is not None:
            rows = []
            results = []
            ts = time.strftime("%Y-%m-%d %H:%M:%S")
            with st.spinner("Running strategies..."):
                for rel in selected:
                    spec = load_config(ROOT / rel)
                    out = run_strategy_on_df(spec, df)
                    results.append(out)
                    rows.append(
                        make_unified_row(
                            timestamp=ts,
                            data_source=data_source,
                            n_ticks=len(df),
                            strategy_result=out,
                            validator_result=None,
                        )
                    )

            st.session_state["last_strategy_results"] = results
            st.session_state["unified_rows"] = rows

            st.success(f"Ran {len(results)} strategy config(s)")
            st.write("### Strategy raw outputs")
            for r in results:
                with st.expander(f"{r.get('strategy_type')} • {r.get('strategy_name')} • {pathlib.Path(r.get('config_path','')).name}"):
                    st.json(r)

            st.write("---")
            st.subheader("Unified comparison table (strategy-only)")
            st.dataframe(rows, use_container_width=True)

            out_path = write_results_csv(rows, ROOT / "results")
            st.success(f"Wrote: {out_path}")
            st.download_button(
                "⬇️ Download results CSV",
                data=pathlib.Path(out_path).read_bytes(),
                file_name=pathlib.Path(out_path).name,
                mime="text/csv",
            )


with tab_validator:
    st.subheader("✅ Validator Sim & Compare")
    st.caption(
        "Run validator simulation on the selected data source, optionally merge with the most recent strategy runs, and export a unified table."
    )

    data_source_v = st.radio("Data Source", ["Synthetic", "CSV Upload"], horizontal=True, key="val_data_source")
    dfv = None
    if data_source_v == "Synthetic":
        n_ticks_v = int(st.number_input("n_ticks", min_value=200, max_value=200000, value=3000, step=100, key="val_n"))
        seed_v = int(st.number_input("seed", min_value=0, max_value=10_000_000, value=123, step=1, key="val_seed"))
        dfv = make_synthetic_df(n_ticks=n_ticks_v, seed=seed_v)
        st.success(f"Synthetic series ready: {len(dfv)} ticks")
    else:
        upv = st.file_uploader("Upload CSV", type=["csv"], key="val_up")
        if upv is not None:
            dfv = read_price_df_from_upload(upv.getvalue(), upv.name)
            st.success(f"CSV series loaded: {len(dfv)} ticks")

    st.write("---")
    validator_kind = st.selectbox("Validator kind", ["EWMA", "Volatility", "Persistence"], index=0)
    st.caption("Tip: use Confirm>1 to require repeated triggers.")

    params = {
        "confirm": int(st.number_input("confirm", min_value=1, max_value=10, value=2, step=1)),
        "latency_ticks": int(st.number_input("latency_ticks", min_value=0, max_value=50, value=1, step=1)),
        "min_interval_ticks": int(st.number_input("min_interval_ticks", min_value=0, max_value=200, value=5, step=1)),
        "max_trades_per_100": int(st.number_input("max_trades_per_100", min_value=1, max_value=200, value=15, step=1)),
        "cost_bps": float(st.number_input("cost_bps", min_value=0.0, max_value=10.0, value=0.5, step=0.1)),
        "slip_bps": float(st.number_input("slip_bps", min_value=0.0, max_value=10.0, value=0.3, step=0.1)),
        "position": float(st.number_input("position", min_value=0.0, max_value=100.0, value=1.0, step=0.5)),
    }

    if validator_kind.upper() == "EWMA":
        params.update(
            {
                "alpha": float(st.number_input("alpha", min_value=0.001, max_value=0.5, value=0.05, step=0.005)),
                "z_enter": float(st.number_input("z_enter", min_value=0.1, max_value=10.0, value=2.5, step=0.1)),
                "z_exit": float(st.number_input("z_exit", min_value=0.1, max_value=10.0, value=1.8, step=0.1)),
            }
        )
    elif validator_kind.upper() == "VOLATILITY":
        params.update(
            {
                "window": int(st.number_input("window", min_value=5, max_value=500, value=50, step=5)),
                "max_vol": float(st.number_input("max_vol", min_value=0.0001, max_value=0.2, value=0.01, step=0.001)),
            }
        )
    else:
        params.update(
            {
                "hold": int(st.number_input("hold", min_value=1, max_value=20, value=3, step=1)),
                "mean_alpha": float(st.number_input("mean_alpha", min_value=0.001, max_value=0.5, value=0.05, step=0.005)),
                "z": float(st.number_input("z", min_value=0.001, max_value=5.0, value=0.2, step=0.01)),
            }
        )

    run_sim = st.button("▶️ Run validator sim")
    if run_sim and dfv is not None:
        with st.spinner("Simulating..."):
            sim_out = run_validator_sim(dfv, validator_kind=validator_kind, params=params)

        st.session_state["last_validator_result"] = sim_out

        st.success("Simulation complete")
        st.write("### Validator metrics")
        st.json({k: sim_out.get(k) for k in ["validator_kind", "total_pnl", "trades", "fsr", "sharpe_like", "max_drawdown", "dd_recovery_ticks"]})

        # Push metrics to Decision tab
        decision_metrics = {
            "sharpe_like": sim_out.get("sharpe_like", 0.0),
            "max_drawdown": sim_out.get("max_drawdown", 0.0),
            "trades": sim_out.get("trades", 0),
            "fsr": sim_out.get("fsr", 0.0),
            "total_pnl": sim_out.get("total_pnl", 0.0),
        }
        st.session_state["metrics_text"] = json.dumps(decision_metrics, indent=2)
        st.info("Decision metrics updated (Decision tab will use these).")

        st.write("### Equity curve")
        st.line_chart(sim_out.get("equity", []))

        st.write("### Trades")
        st.dataframe(sim_out.get("trades_detail", []), use_container_width=True)

        st.write("---")
        st.subheader("Unified comparison table")

        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        rows = []
        last_strat = st.session_state.get("last_strategy_results", [])
        if last_strat:
            for sr in last_strat:
                rows.append(
                    make_unified_row(
                        timestamp=ts,
                        data_source=data_source_v,
                        n_ticks=len(dfv),
                        strategy_result=sr,
                        validator_result=sim_out,
                    )
                )
        else:
            rows.append(
                make_unified_row(
                    timestamp=ts,
                    data_source=data_source_v,
                    n_ticks=len(dfv),
                    strategy_result=None,
                    validator_result=sim_out,
                )
            )

        st.session_state["unified_rows"] = rows
        st.dataframe(rows, use_container_width=True)

        out_path = write_results_csv(rows, ROOT / "results")
        st.success(f"Wrote: {out_path}")
        st.download_button(
            "⬇️ Download results CSV",
            data=pathlib.Path(out_path).read_bytes(),
            file_name=pathlib.Path(out_path).name,
            mime="text/csv",
        )


st.write("---")
st.caption(
    "Tip: Run Streamlit from the repo root (or set PYTHONPATH=.) so modules can be discovered. In AWS mode ensure a valid AWS profile and Bedrock model access."
)
