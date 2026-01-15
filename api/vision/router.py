from fastapi import APIRouter, File, UploadFile, HTTPException
from .model import detector
from .ttc import estimate_ttc
from .ocr_reader import ocr_reader
import io

router = APIRouter()

@router.post('/detect')
async def detect(file: UploadFile = File(...)):
    """Accepts an image file (jpeg/png) and returns detections."""
    content = await file.read()
    # In a real system, you'd convert bytes to image and run detector.
    detections = detector.detect(content)
    return {'detections': detections}

@router.post('/estimate_ttc')
async def ttc(distance_m: float, relative_speed_m_s: float):
    """Estimate TTC given distance and relative speed."""
    t = estimate_ttc(distance_m, relative_speed_m_s)
    return {'ttc_seconds': t}

@router.post('/read_text')
async def read_text(file: UploadFile = File(...)):
    """قراءة النصوص من صورة (OCR) - يدعم العربية والإنجليزية"""
    content = await file.read()
    
    texts = ocr_reader.read_text(content)
    combined_text = ocr_reader.get_combined_text(texts)
    
    return {
        'texts': texts,
        'combined_text': combined_text,
        'count': len(texts),
        'has_text': len(texts) > 0
    }
