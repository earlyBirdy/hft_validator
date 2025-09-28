# HFT Validator Framework with AWS Agent Extension

This repo contains:
- C++ backtester & validators
- Python AI agent for local parameter tuning
- AWS Hackathon extension:
  - Bedrock agent scaffold (`python/agent_bedrock.py`)
  - Lambda handler (`aws/lambda_handler.py`)
  - Deployment instructions (`aws/deploy_instructions.md`)

## Hackathon Submission Checklist
- [x] Public repo (this)
- [x] Architecture diagram (add PNG to `aws/architecture.png`)
- [x] Demo video (show baseline vs agent-driven run)
- [x] Deployed API Gateway endpoint
- [x] README description with quantified improvements

## Run locally
```bash
./run.sh
```

## Env vars
- `AGENT_IMPL=local|bedrock` (default local)
- `AGENT_MODE=smart|fixed` (default smart)
- `USE_BEDROCK=1` to call Bedrock in bedrock agent
- `DATA_PATH=data/sample_prices.csv`

## AWS thin adapter
```bash
sam build && sam deploy --guided
curl -X POST "$API_URL/decision" -d '{}' -H "Content-Type: application/json"
```

## Layout
- `app/` (backtester, strategies, agents)
- `cli.py` (prints JSON with baseline, smart, agent hint, final, and Sharpe improvement)
- `lambda_handler.py` (Lambda entry)
- `infra/sam/template.yaml`
- `data/sample_prices.csv`

---

## Available Strategies / Validators

List them:
```bash
python3 cli.py --list-strategies
```

Current registry:
- **EWMA** — EWMA band breakout with volatility bands (params: `alpha`, `threshold`, `window`)
- **PERSIST** — Directional persistence / hold strategy (params: `hold_period`)

---

## HTML Report Generator

Create a simple report (equity plot + metrics + params):
```bash
# inside your venv
python3 cli.py --report report.html
# open report.html
```
