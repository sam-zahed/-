# PowerShell script to download models (Option B)
$root = Split-Path -Parent $MyInvocation.MyCommand.Definition
$models = Join-Path $root "app\models"
New-Item -ItemType Directory -Force -Path $models | Out-Null
Write-Host "Installing python packages..."
python -m pip install --upgrade pip
python -m pip install ultralytics faster-whisper
$yolo = "https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8s.pt"
$yolopath = Join-Path $models "yolov8s.pt"
if (!(Test-Path $yolopath)) { Invoke-WebRequest -Uri $yolo -OutFile $yolopath }
Write-Host "Downloading whisper-base via faster-whisper..."
python - <<'PY'
from faster_whisper import download_model
import os
MODEL_DIR = os.path.join(os.path.dirname(__file__), 'app', 'models', 'whisper-base')
os.makedirs(MODEL_DIR, exist_ok=True)
print('Downloading whisper-base into', MODEL_DIR)
download_model('openai/whisper-base', MODEL_DIR)
PY
Write-Host "Done."
