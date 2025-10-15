import os, sys, json, time, importlib, traceback
from typing import Dict, Any, Callable, List, Tuple
import pathlib
import streamlit as st

# Ensure repo root is importable even if Streamlit runs from another CWD
ROOT = pathlib.Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

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

st.subheader("📊 Input Metrics (JSON)")
example = {"sharpe_like": 0.8, "drawdown": 0.05, "trades": 120}
if st.sidebar.button("Load Example Metrics"):
    st.session_state["metrics_text"] = json.dumps(example, indent=2)
metrics_text = st.text_area("Provide recent trading metrics as JSON", value=st.session_state.get("metrics_text", json.dumps(example, indent=2)), height=200)

col1, col2 = st.columns([1,1])
run_clicked = col1.button("🚀 Run Decision")
clear_clicked = col2.button("🧹 Clear Output")

if clear_clicked:
    for k in ["last_output_text", "last_error", "last_engine"]:
        st.session_state.pop(k, None)
    st.rerun()

def set_mode_env(mode: str, region: str, model_id: str):
    if mode.startswith("Local"):
        os.environ["HFT_AGENT_DRYRUN"] = "1"
    else:
        if "HFT_AGENT_DRYRUN" in os.environ:
            del os.environ["HFT_AGENT_DRYRUN"]
        os.environ["AWS_REGION"] = region.strip()
        os.environ["BEDROCK_MODEL_ID"] = model_id.strip()

st.write("---")
st.subheader("🧠 Decision Output")
if AVAILABLE:
    st.info(f"Active engine: **{validator_choice}** | Mode: **{mode}**")

def as_json(s: str) -> Dict[str, Any]:
    try:
        return json.loads(s)
    except Exception as e:
        raise ValueError(f"Invalid JSON for metrics: {e}")

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

st.write("---")
st.caption("Tip: Run Streamlit from the repo root or set PYTHONPATH=. so modules can be discovered. In AWS mode ensure a valid AWS profile and Bedrock model access.")
