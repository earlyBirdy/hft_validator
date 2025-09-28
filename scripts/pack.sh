#!/usr/bin/env bash
set -euo pipefail
OUT=${1:-hft_validator_clean.zip}

# Create a lightweight zip excluding venvs, caches, reports, data & SAM builds
zip -r "$OUT" . \
  -x ".git/*" \
  -x ".venv/*" ".venv311/*" "env/*" "venv/*" \
  -x "__pycache__/*" ".pytest_cache/*" "*.py[cod]" "*.pyo" "*.pyd" "*.so" "*.egg-info/*" \
  -x ".DS_Store" "Thumbs.db" \
  -x "report*.html" "*.png" "*.jpg" "*.pdf" "*.zip" \
  -x "data/*.csv" \
  -x ".aws-sam/*" "infra/.aws-sam/*"
echo "Wrote $OUT"
