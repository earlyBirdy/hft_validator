# HFT Validator - AWS Bedrock Agent Architecture

This project integrates a Bedrock-hosted LLM as a decision agent for a high-frequency trading (HFT) backtester.
The agent receives recent trading metrics (e.g., Sharpe-like ratio, drawdown, trade count) and returns a validator
choice with tuned parameters, which are then applied to the next backtest run.

## Components
- Local Dev & Backtester (CLI/Streamlit): Runs strategies and produces metrics JSON.
- Amazon API Gateway: Public endpoint `/decision` that forwards to Lambda.
- AWS Lambda (Agent Runner): Invokes the Bedrock model using `python/agent_bedrock.py` and returns a JSON decision.
- Amazon Bedrock: Foundation model (LLM) that reasons over the metrics and suggests validator + params.
- Amazon S3 (Optional): Persist metrics, decisions, and reports for reproducibility and judging.

## Data Flow
1. Backtester computes metrics locally.
2. Client sends POST /decision (API Gateway) with {"metrics": {...}}.
3. Lambda calls Bedrock InvokeModel and parses a strict JSON decision.
4. Decision is returned to the client and applied in the next run.
5. (Optional) metrics/decisions/reports are written to S3.

## Deployment Notes
- Package `aws/lambda_handler.py` and `python/agent_bedrock.py` into `function.zip`.
- Lambda IAM Role must include `bedrock:InvokeModel` for the chosen model and region.
- Set env vars: AWS_REGION, BEDROCK_MODEL_ID (choose a model you have access to).
- For local dev without AWS, the agent falls back to a deterministic default decision.
