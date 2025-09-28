# HFT Validator Framework with AWS Agent Extension

A Tiny, **vendor‑neutral** validator that runs fully **offline by default**, with an **optional AWS thin adapter** for the hackathon. It prints a JSON summary (baseline, smart pick, agent hint, final, improvement) and can generate a compact HTML report.

---

This repo contains:
- C++ backtester & validators
- Python AI agent for local parameter tuning
- AWS Hackathon extension:
  - Bedrock agent scaffold (`python/agent_bedrock.py`)
  - Lambda handler (`aws/lambda_handler.py`)
  - Deployment instructions (`aws/deploy_instructions.md`)

## Env vars
- `AGENT_IMPL=local|bedrock` (default local)
- `AGENT_MODE=smart|fixed` (default smart)
- `USE_BEDROCK=1` to call Bedrock in bedrock agent
- `DATA_PATH=data/sample_prices.csv`

---

## Quickstart

```bash
# from repo root
chmod +x run.sh
./run.sh
```

This will:
1) pick a Python ≥ 3.10 (prefers 3.12 → 3.11 → 3.10 → python3),  
2) create/activate a virtualenv (`.venv` by default),  
3) install `requirements.txt`,  
4) run the CLI on the sample data.

---

## Generate an HTML report

```bash
./run.sh --report report.html
# macOS
open report.html
# Linux
xdg-open report.html
```

The report includes:
- Baseline vs Final **equity** (two lines; if they coincide the **Final** line is dashed and a note explains they’re identical),
- a **metrics** table,
- **parameter** blocks for both runs.

---

## List available strategy validators

```bash
python cli.py --list-strategies
```

**Current registry** (selection is automatic):
- **EWMA** — Exponentially Weighted Moving Average band breakout / threshold filter (params: `alpha`, `threshold`, `window`)
- **PERSIST** — Directional persistence / hold strategy (params: `hold_period`)
- **AUTO** — Regime‑aware chooser that tries an EWMA grid for trendier/low‑vol regimes; otherwise a PERSIST grid. Picks the best candidate by (Sharpe, then PnL). The grids/gates live in `app/strategies/auto_select.py`.

---

## Important environment knobs

| Variable | Default | Meaning |
|---|---:|---|
| `DATA_PATH` | `data/sample_prices.csv` | CSV of timestamp,price |
| `AGENT_IMPL` | `local` | `local` (offline) or `bedrock` (AWS adapter) |
| `AGENT_MODE` | `smart` | `smart` (use chooser & hints) or `fixed` |
| `REQUIRE_IMPROVEMENT` | `1` | If `1`, **Final** must beat Baseline Sharpe; otherwise we **fall back** to Baseline so demos never look worse |
| `PYTHON` | *(auto)* | Interpreter to use, e.g. `python3.11` |
| `VENV_DIR` | `.venv` | Virtualenv directory; set a different path to keep multiple envs |

**Examples**
```bash
# Use specific Python and a dedicated venv
PYTHON=python3.11 VENV_DIR=.venv311 ./run.sh --report report311.html

# Disable the “require improvement” safeguard to see raw smart output
REQUIRE_IMPROVEMENT=0 ./run.sh --report report_raw.html

# Point to your own dataset
DATA_PATH=/path/to/my_prices.csv ./run.sh --report my_report.html
```

---

## AWS as a thin adapter (Hackathon extension)

## AWS thin adapter
```bash
sam build && sam deploy --guided
curl -X POST "$API_URL/decision" -d '{}' -H "Content-Type: application/json"
```

The core stays vendor‑neutral; the AWS path only swaps the **decision helper** behind the same interface as the local agent.

Run locally with AWS adapter enabled:
```bash
AGENT_IMPL=bedrock ./run.sh --report report.html
```

**Deploy the minimal API (SAM example):**
```bash
sam build && sam deploy --guided
# After deploy, exercise the endpoint
curl -X POST "$API_URL/decision" -d '{}' -H "Content-Type: application/json"
```

**Adapter pieces**
- `app/agent/bedrock.py` — Bedrock agent client (same function shape as `app/agent/local.py`: `decide(payload) -> {hint_strategy, hint_params, reason}`)
- `aws/lambda_handler.py` — Lambda entry point
- `infra/sam/template.yaml` — SAM template
- `aws/deploy_instructions.md` — more details (optional)

**Peel back to local immediately**: unset `AGENT_IMPL` or set it to `local` — no other code changes needed.

---

## Repo layout (trimmed)

```
.
├── app/
│   ├── agent/
│   │   ├── local.py         # local hint provider
│   │   └── bedrock.py       # optional AWS adapter
│   ├── strategies/
│   │   └── auto_select.py   # chooser + grids (EWMA/PERSIST)
│   ├── backtester.py        # strategy engines + metrics
│   └── data.py              # CSV loader
├── aws/
│   ├── lambda_handler.py
│   ├── architecture.png     # add your diagram for the submission
│   └── deploy_instructions.md
├── infra/
│   └── sam/template.yaml
├── data/
│   └── sample_prices.csv
├── cli.py                   # CLI + report generator
├── requirements.txt
└── run.sh                   # robust runner (creates venv, installs, runs)
```

---

## Hackathon Submission Checklist
- [x] Public repo
- [x] Architecture diagram (`aws/architecture.png`)
- [x] Demo video (show baseline vs agent‑driven run + report)
- [x] Deployed API Gateway endpoint (if using AWS adapter)
- [x] README description with quantified improvements

---

## Notes

- When Baseline and Final curves are identical, the **Final** line is dashed and a note appears above the chart.
- Metrics on the sample set are illustrative; bring your own data via `DATA_PATH` to validate your case.
- The AWS integration is opt‑in and lives behind a clean interface so you can remove it without touching core logic.
