#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
MODELDIR="$ROOT/models"
mkdir -p "$MODELDIR"
echo "Installing Python packages (ultralytics, faster-whisper)..."
python3 -m pip install --upgrade pip
python3 -m pip install ultralytics faster-whisper

# Download YOLOv8s weights (ultralytics official)
YOLO_URL="https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8s.pt"
if [ ! -f "$MODELDIR/yolov8s.pt" ]; then
  echo "Downloading yolov8s.pt (~22 MB)..."
  curl -L "$YOLO_URL" -o "$MODELDIR/yolov8s.pt"
else
  echo "yolov8s.pt already exists."
fi

# Download Whisper 'base' model using faster-whisper's downloader (HuggingFace files)
echo "Downloading Whisper 'base' model (may be ~140 MB)..."
python3 - <<PY
from faster_whisper import download_model
import os
MODEL_DIR = os.path.join(os.path.dirname(__file__), 'models', 'whisper-base')
os.makedirs(MODEL_DIR, exist_ok=True)
print('Downloading whisper-base into', MODEL_DIR)
download_model('openai/whisper-base', MODEL_DIR)
PY

echo "All models downloaded to $MODELDIR"
echo "NOTE: If download fails due to authentication or bandwidth, download manually from HuggingFace and place into $MODELDIR/whisper-base"
