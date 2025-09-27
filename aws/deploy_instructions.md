# AWS Hackathon Deployment Instructions

## Requirements
- AWS account with Bedrock + Lambda access
- AWS CLI configured
- Python 3.9+

## Steps
1. Deploy Lambda
   ```bash
   zip function.zip python/agent_bedrock.py aws/lambda_handler.py
   aws lambda create-function --function-name AgentValidator      --runtime python3.9 --role <ROLE_ARN>      --handler lambda_handler.lambda_handler --zip-file fileb://function.zip
   ```

2. API Gateway Integration
   - Create a new API Gateway endpoint linked to the Lambda.
   - This will expose `/decision` to trigger the agent.

3. S3 & Results
   - Configure an S3 bucket to store backtester results and configs.
   - Agent writes config.json, backtester reads it.

4. Demo Flow
   - Run `./run.sh` locally for baseline results.
   - Call API Gateway `/decision` to get Bedrock agent decision.
   - Update backtester config with decision and rerun.

## Notes
- The included `agent_bedrock.py` is mocked locally for demo.
- Replace with actual BedrockRuntime client for live submission.
