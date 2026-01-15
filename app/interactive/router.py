from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from app.audio.transcribe import transcribe_audio_bytes
from app.vision.model import detector
import base64
import numpy as np
import cv2
import re

router = APIRouter()

@router.post('/interactive/learn')
async def learn_from_voice(
    audio: UploadFile = File(...),
    image: str = Form(...) # Base64 image
):
    """
    Receives audio voice note + current image.
    Transcribes audio to extract name.
    Learns the face in the image with that name.
    """
    # 1. Transcribe
    content = await audio.read()
    text = transcribe_audio_bytes(content)
    print(f"👂 Heard: {text}")
    
    if not text or "[" in text: # [empty] or [mock]
        return {"status": "error", "message": "Could not hear clear speech"}

    # 2. Extract Name
    # Heuristic regex
    name = None
    
    # English patterns
    patterns = [
        r"this is ([\w\s]+)",
        r"name is ([\w\s]+)",
        r"call him ([\w\s]+)",
        r"call her ([\w\s]+)"
    ]
    
    for p in patterns:
        m = re.search(p, text.lower())
        if m:
            name = m.group(1)
            break
            
    # Arabic patterns (simple containment)
    if not name:
        if "هذا" in text:
            name = text.split("هذا")[-1].strip()
        elif "هذه" in text:
            name = text.split("هذه")[-1].strip()
        elif "اسمه" in text:
            name = text.split("اسمه")[-1].strip()
            
    # Fallback: if short text, assume it's just the name (e.g. "Ahmed")
    if not name and len(text.split()) <= 2:
        name = text
        
    if not name:
        return {"status": "error", "message": "Could not understand name from audio", "text": text}
        
    name = name.strip()
    
    # 3. Process Image
    try:
        if "base64," in image:
            image = image.split("base64,")[1]
            
        img_bytes = base64.b64decode(image)
        arr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    except Exception as e:
        return {"status": "error", "message": "Invalid image data"}
        
    # 4. Save Face
    if hasattr(detector, 'face_manager'):
        success, msg = detector.face_manager.save_face(img_rgb, name)
        if success:
            return {"status": "success", "message": f"Learned: {name}", "name": name}
        else:
            return {"status": "error", "message": msg}
    else:
        return {"status": "error", "message": "Face recognition not initialized"}
