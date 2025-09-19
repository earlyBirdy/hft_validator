#!/bin/bash
set -e

echo "[1/3] Building C++ backtester..."
make

echo "[2/3] Running AI agent to tune parameters..."
python3 python/ai_agent.py

echo "[3/3] Running backtester with default params..."
./backtester
