# Option B - Details & Run Notes

1. Ensure you have enough disk space (~200-400MB) for the Whisper base model and YOLOv8s weights.
2. Recommended: run in a Python virtualenv or Docker. In Docker, the download script will also work if `curl` and python available.
3. Commands:
   - `./download_models.sh`
   - `./deploy.sh` (or `docker compose up --build`)
4. If you have a GPU and CUDA, you can adjust faster-whisper to use device='cuda' and install GPU-compatible wheels.
5. TTS uses pyttsx3 which may rely on system audio backends. For server-side TTS, consider Coqui TTS or an external API.
