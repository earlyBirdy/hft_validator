#!/usr/bin/env bash
set -euo pipefail
rm -rf .venv .venv311 env venv
find . -name "__pycache__" -type d -prune -exec rm -rf {} +
rm -rf .pytest_cache .mypy_cache .cache .coverage htmlcov
rm -rf .aws-sam infra/.aws-sam
rm -f report*.html *.zip
echo "Cleaned local artifacts."
