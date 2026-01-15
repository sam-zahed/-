
print("--- Testing gTTS ---")
try:
    from gtts import gTTS
    tts = gTTS("test", lang='en')
    tts.save("/tmp/test_gtts.mp3")
    print("✅ gTTS Success")
except Exception as e:
    print(f"❌ gTTS Failed: {e}")

print("--- Testing pyttsx3 ---")
try:
    import pyttsx3
    engine = pyttsx3.init()
    engine.save_to_file("test", "/tmp/test_pyttsx3.wav")
    engine.runAndWait()
    print("✅ pyttsx3 Success")
except Exception as e:
    print(f"❌ pyttsx3 Failed: {e}")

print("--- Testing faster-whisper ---")
try:
    from faster_whisper import WhisperModel
    model = WhisperModel("base", device='cpu', compute_type='int8')
    print("✅ faster-whisper Load Success")
except Exception as e:
    print(f"❌ faster-whisper Load Failed: {e}")
