# Audio Module

- /audio/asr accepts audio file and returns text (uses placeholder).
- /audio/tts accepts json {text: '...'} and returns an audio stream (placeholder).

To use Whisper locally, install `openai-whisper` or `faster-whisper` and replace `transcribe_audio_bytes`.
