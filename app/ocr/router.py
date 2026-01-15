from fastapi import APIRouter, File, UploadFile
from app.vision.ocr_reader import ocr_reader
import base64
import numpy as np
import cv2

router = APIRouter()

@router.post('/ocr/read')
async def read_text_from_image(image: UploadFile = File(...)):
    """
    Extract text from image using EasyOCR
    """
    try:
        # Read image
        content = await image.read()
        arr = np.frombuffer(content, np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        
        if img is None:
            return {"status": "error", "message": "Invalid image"}
        
        # Run OCR
        if hasattr(ocr_reader, 'readtext'):
            results = ocr_reader.readtext(img)
            
            # Extract text
            texts = [text for (bbox, text, conf) in results if conf > 0.3]
            full_text = " ".join(texts)
            
            if full_text:
                return {"status": "success", "text": full_text, "count": len(texts)}
            else:
                return {"status": "success", "text": "", "message": "No text found"}
        else:
            return {"status": "error", "message": "OCR not initialized"}
            
    except Exception as e:
        return {"status": "error", "message": str(e)}
