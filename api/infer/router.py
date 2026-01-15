from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import base64
from app.vision.model import detector
from app.alerts.priority_system import process_detections_with_alerts, get_summary_message
import time

router = APIRouter()

class InferRequest(BaseModel):
    event_id: str
    user_id: str
    small_image_b64: str
    depth_summary: Optional[Dict[str, Any]] = None
    device_pose: Optional[Dict[str, Any]] = None
    priority: Optional[str] = "normal"
    lang: Optional[str] = "ar" # 'ar' or 'da'

@router.post('/realtime')
async def realtime_infer(request: InferRequest):
    """
    Simulates the /infer/realtime endpoint expected by n8n.
    Decodes the base64 image and runs the vision model.
    """
    try:
        # Decode base64 image
        if "," in request.small_image_b64:
             header, encoded = request.small_image_b64.split(",", 1)
        else:
             encoded = request.small_image_b64
        
        image_data = base64.b64decode(encoded)
        
        # Run detection
        # Note: detector.detect usually expects raw bytes, so this should work if implemented correctly
        start_time = time.time()
        detections = detector.detect(image_data, target_lang=request.lang) 
        inference_time = (time.time() - start_time) * 1000

        # Construct response format expected by n8n
        # N8N expects: objects, TTC, scene_confidence, inference_time_ms, model_version
        
        objects = []
        for det in detections:
            # map keys if necessary. 
            # DummyDetector/YoloDetector output: class, conf, bbox, distance_m (optional)
            
            # MOCK DISTANCE for demo purposes if not present
            dist = det.get('distance_m')
            if dist is None:
                 # Mock distance based on bounding box size (larger box = closer)
                 bbox = det.get('bbox', [0,0,0,0])
                 # simple heuristic: box height
                 h = bbox[3] - bbox[1] if bbox else 100
                 dist = max(1.0, 1000.0 / (h + 1.0))

            objects.append({
                "class": det.get('class', 'unknown'),
                "class_ar": det.get('class_ar', det.get('class', 'unknown')),
                "conf": det.get('conf', 0.0),
                "confidence": det.get('conf', 0.0),
                "bbox": det.get('bbox', [0,0,0,0]),
                "distance_m": dist
            })

        # معالجة التنبيهات الذكية
        alerts_data = await process_detections_with_alerts(objects, image_width=640)
        
        return {
            "objects": objects,
            "alerts": alerts_data['all_alerts'],
            "critical_alerts": alerts_data['critical_alerts'],
            "speak_message": alerts_data['speak_message'],
            "summary": get_summary_message(alerts_data),
            "has_danger": alerts_data['has_danger'],
            "object_count": alerts_data['object_count'],
            "TTC": 999.0,
            "scene_confidence": 0.8,
            "inference_time_ms": inference_time,
            "model_version": "yolov8-world-v2"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
