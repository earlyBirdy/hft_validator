CXX=g++
CXXFLAGS=-O2 -std=c++17

all: backtester

backtester: cpp/main.cpp
	$(CXX) $(CXXFLAGS) -o backtester cpp/main.cpp

clean:
	rm -f backtester


# --- Hackathon targets ---
.PHONY: hackathon sam-build sam-deploy

hackathon: sam-build sam-deploy

sam-build:
	sam build --use-container --template-file infra/sam/template.yaml

sam-deploy:
	STACK_NAME?=HFTValidatorStack
	AWS_REGION?=us-east-1
	BEDROCK_MODEL_ID?=anthropic.claude-3-5-sonnet-20241022-v2:0
	LAMBDA_FUNCTION_NAME?=HFTAgentValidator
	sam deploy --stack-name $(STACK_NAME) --resolve-s3 --capabilities CAPABILITY_IAM --no-fail-on-empty-changeset \
		--parameter-overrides AwsRegion=$(AWS_REGION) BedrockModelId=$(BEDROCK_MODEL_ID) LambdaFunctionName=$(LAMBDA_FUNCTION_NAME)
