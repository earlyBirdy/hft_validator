#!/usr/bin/env bash
set -euo pipefail

STACK_NAME="${STACK_NAME:-HFTValidatorStack}"
AWS_REGION="${AWS_REGION:-us-east-1}"
BEDROCK_MODEL_ID="${BEDROCK_MODEL_ID:-anthropic.claude-3-5-sonnet-20241022-v2:0}"
LAMBDA_FUNCTION_NAME="${LAMBDA_FUNCTION_NAME:-HFTAgentValidator}"

echo "[1/3] Building SAM package..."
sam build --use-container --template-file infra/sam/template.yaml

echo "[2/3] Deploying stack: ${STACK_NAME} (region: ${AWS_REGION})"
sam deploy   --stack-name "${STACK_NAME}"   --resolve-s3   --capabilities CAPABILITY_IAM   --no-fail-on-empty-changeset   --parameter-overrides     AwsRegion="${AWS_REGION}"     BedrockModelId="${BEDROCK_MODEL_ID}"     LambdaFunctionName="${LAMBDA_FUNCTION_NAME}"

echo "[3/3] Done."
echo "Tip: To invoke locally:"
echo "  aws lambda invoke --function-name ${LAMBDA_FUNCTION_NAME} --payload '{"metrics":{"sharpe_like":0.8,"drawdown":0.05,"trades":120}}' out.json && cat out.json"
