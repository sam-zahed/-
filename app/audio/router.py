from fastapi import APIRouter, File, UploadFile, HTTPException
from .transcribe import transcribe_audio_bytes
from .tts import synthesize_text
from fastapi.responses import StreamingResponse
import io

router = APIRouter()

@router.post('/asr')
async def asr(file: UploadFile = File(...)):
    content = await file.read()
    text = transcribe_audio_bytes(content)
    return {'text': text}

@router.post('/tts')
async def tts(payload: dict):
    text = payload.get('text','')
    audio_bytes = synthesize_text(text)
    return StreamingResponse(io.BytesIO(audio_bytes), media_type='audio/wav')
