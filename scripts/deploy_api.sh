#!/usr/bin/env bash
set -euo pipefail
: "${STACK_NAME:=HFTValidatorStack}"
: "${AWS_REGION:=us-east-1}"
: "${BEDROCK_MODEL_ID:=anthropic.claude-3-5-sonnet-20241022-v2:0}"
: "${LAMBDA_FUNCTION_NAME:=HFTAgentValidator}"
sam build --use-container --template-file infra/sam/template.yaml
sam deploy --stack-name "$STACK_NAME" --resolve-s3 --capabilities CAPABILITY_IAM --no-fail-on-empty-changeset   --parameter-overrides AwsRegion="$AWS_REGION" BedrockModelId="$BEDROCK_MODEL_ID" LambdaFunctionName="$LAMBDA_FUNCTION_NAME"
echo "Invoke: aws lambda invoke --function-name $LAMBDA_FUNCTION_NAME --payload '{"metrics":{"sharpe_like":0.8,"drawdown":0.05,"trades":120}}' out.json && cat out.json"
