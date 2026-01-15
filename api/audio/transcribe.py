# ASR using faster-whisper (whisper-base) with fallback to mock transcription.
import os
from pathlib import Path
MODELDIR = Path('/code/models')

def transcribe_audio_bytes(b: bytes) -> str:
    # Try faster-whisper if model available
    try:
        from faster_whisper import WhisperModel
        # Use model name "base" with download_root pointing to our models dir
        model = WhisperModel("base", device='cpu', compute_type='int8', download_root=str(MODELDIR))
        
        # write bytes to temp file
        import tempfile
        tf = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        tf.write(b)
        tf.flush()
        tf.close()
        
        result = model.transcribe(tf.name, beam_size=5)
        segments = [s.text for s in result[0]]
        
        os.unlink(tf.name)
        return " ".join(segments) if segments else "[empty]"
    except Exception as e:
        return f"[mock transcription: faster-whisper unavailable: {e}]"
