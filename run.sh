#!/usr/bin/env bash
set -Eeuo pipefail

OS="$(uname -s || echo Unknown)"
echo "🖥  OS: $OS"

# 1) Pick a Python (allow override)
CANDIDATES=()
if [ -n "${PYTHON:-}" ]; then
  CANDIDATES+=("$PYTHON")
fi
CANDIDATES+=("python3.12" "python3.11" "python3.10" "python3")

FIND_PY=""
for p in "${CANDIDATES[@]}"; do
  if command -v "$p" >/dev/null 2>&1; then
    if "$p" -c 'import sys; exit(0 if sys.version_info[:2] >= (3,10) else 1)'; then
      FIND_PY="$p"
      break
    fi
  fi
done

if [ -z "$FIND_PY" ]; then
  echo "❌ Could not find Python >= 3.10."
  if [ "$OS" = "Darwin" ]; then
    echo "👉 On macOS, install Homebrew Python then retry:"
    echo '   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
    echo "   brew install python@3.11"
    echo "   PYTHON=/opt/homebrew/bin/python3 ./run.sh   # (Apple Silicon)"
    echo "   PYTHON=/usr/local/bin/python3 ./run.sh      # (Intel Mac)"
  else
    echo "👉 Install Python 3.11+ and retry."
  fi
  exit 1
fi

echo "🐍 Using Python: $FIND_PY ($("$FIND_PY" -c 'import sys; print(sys.version)'))"

# 2) Create venv if missing (try stdlib venv, then virtualenv fallback)
VENV="${VENV_DIR:-.venv}"
if [ ! -d "$VENV" ]; then
  echo "🔧 Creating virtual environment in $VENV"
  if ! "$FIND_PY" -m venv "$VENV" 2>/dev/null; then
    echo "   Stdlib venv failed; trying virtualenv fallback..."
    "$FIND_PY" -m pip install --user --upgrade pip virtualenv >/dev/null
    "$FIND_PY" -m virtualenv "$VENV"
  fi
fi

# 3) Activate venv (posix + Git Bash on Windows)
if [ -f "$VENV/bin/activate" ]; then
  # shellcheck disable=SC1090
  source "$VENV/bin/activate"
elif [ -f "$VENV/Scripts/activate" ]; then
  # shellcheck disable=SC1090
  source "$VENV/Scripts/activate"
else
  echo "❌ Could not find venv activation script in $VENV"
  echo "   Contents of $VENV:"
  ls -la "$VENV" || true
  if [ "$OS" = "Darwin" ]; then
    echo "👉 macOS tips:"
    echo "   - Ensure you're using Homebrew Python (brew install python@3.11)"
    echo "   - Then retry with: PYTHON=\$(brew --prefix)/bin/python3 ./run.sh"
  fi
  exit 1
fi

# 4) Install deps
echo "📦 Installing requirements..."
pip install --upgrade pip >/dev/null
pip install -r requirements.txt

# 5) Run CLI (pass-through args like --report report.html)
export DATA_PATH="${DATA_PATH:-data/sample_prices.csv}"
echo "▶️  Running CLI..."
"$FIND_PY" cli.py "$@"
