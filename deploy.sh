#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
python3 -m venv "$ROOT/.venv"
source "$ROOT/.venv/bin/activate"
pip install --upgrade pip
pip install -r "$ROOT/requirements.txt"
echo "Starting uvicorn... (http://0.0.0.0:8000)"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
