import os
from pathlib import Path

def download_whisper():
    print("⬇️ Downloading Whisper model (base)...")
    # Create models directory
    models_dir = Path("/code/models")
    models_dir.mkdir(parents=True, exist_ok=True)
    
    # Download using faster-whisper's built-in download
    # This will download to the cache, then we copy to our models dir
    try:
        from faster_whisper import WhisperModel, download_model
        
        # Download to default cache first
        model_path = download_model("base", cache_dir=str(models_dir))
        print(f"✅ Whisper model downloaded to: {model_path}")
        
        # Test load
        model = WhisperModel("base", device="cpu", compute_type="int8", download_root=str(models_dir))
        print("✅ Whisper model verified and ready.")
    except Exception as e:
        print(f"⚠️ Whisper download failed: {e}")
        print("   Will use fallback transcription.")

if __name__ == "__main__":
    download_whisper()
