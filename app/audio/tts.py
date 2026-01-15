# TTS - Text to Speech
# تحويل النص لصوت
# يدعم العربية عبر gTTS

def synthesize_text(text: str, lang: str = 'ar') -> bytes:
    """
    تحويل النص لصوت
    
    Args:
        text: النص المراد تحويله
        lang: اللغة ('ar' للعربية، 'en' للإنجليزية)
    
    Returns:
        bytes: ملف صوتي WAV
    """
    if not text:
        return b''
    
    # محاولة 1: gTTS (أفضل للعربية)
    try:
        from gtts import gTTS
        import tempfile
        import os
        
        tts = gTTS(text=text, lang=lang, slow=False)
        
        fd, path = tempfile.mkstemp(suffix='.mp3')
        os.close(fd)
        
        tts.save(path)
        
        with open(path, 'rb') as f:
            data = f.read()
        
        os.remove(path)
        return data
        
    except Exception as e:
        print(f"⚠️ gTTS error: {e}")
    
    # محاولة 2: pyttsx3 (Fallback)
    try:
        import pyttsx3
        import tempfile
        import os
        
        engine = pyttsx3.init()
        
        # محاولة ضبط صوت عربي
        voices = engine.getProperty('voices')
        for voice in voices:
            if 'arabic' in voice.name.lower() or 'ar' in voice.id.lower():
                engine.setProperty('voice', voice.id)
                break
        
        fd, path = tempfile.mkstemp(suffix='.wav')
        os.close(fd)
        
        engine.save_to_file(text, path)
        engine.runAndWait()
        
        with open(path, 'rb') as f:
            data = f.read()
        
        os.remove(path)
        return data
        
    except Exception as e:
        print(f"⚠️ pyttsx3 error: {e}")
        return b''


def synthesize_text_streaming(text: str, lang: str = 'ar'):
    """
    Stream TTS - للتشغيل المباشر
    """
    return synthesize_text(text, lang)
