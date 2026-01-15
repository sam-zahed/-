from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uuid, base64, io, os, json, datetime
from PIL import Image
from typing import Optional
import pathlib

app = FastAPI(title="n8n Assistive Agent - FastAPI microservice")

STORAGE_DIR = pathlib.Path("/data_storage")
TMP_DIR = STORAGE_DIR / "tmp"
EVENTS_DIR = STORAGE_DIR / "events"
CHANGE_DIR = STORAGE_DIR / "change_queue"
TTS_DIR = STORAGE_DIR / "tts"

for d in (TMP_DIR, EVENTS_DIR, CHANGE_DIR, TTS_DIR):
    d.mkdir(parents=True, exist_ok=True)

class RealtimeRequest(BaseModel):
    event_id: Optional[str]
    user_id: str
    small_image_b64: Optional[str] = None
    depth_summary: Optional[dict] = None
    device_pose: Optional[dict] = None

@app.post('/upload_tmp')
async def upload_tmp(image_b64: str):
    try:
        header, data = image_b64.split(',', 1) if ',' in image_b64 else (None, image_b64)
        b = base64.b64decode(data)
        img = Image.open(io.BytesIO(b)).convert('RGB')
        fname = f"{uuid.uuid4()}.jpg"
        path = TMP_DIR / fname
        img.save(path, format='JPEG', quality=60)
        return {"tmp_uri": str(path)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post('/infer/realtime')
async def infer_realtime(req: RealtimeRequest):
    # NOTE: placeholder inference logic. Replace with real model calls.
    # If image provided, store temporarily
    if req.small_image_b64:
        header, data = req.small_image_b64.split(',', 1) if ',' in req.small_image_b64 else (None, req.small_image_b64)
        try:
            b = base64.b64decode(data)
            img = Image.open(io.BytesIO(b)).convert('RGB')
            fname = f"{uuid.uuid4()}.jpg"
            path = TMP_DIR / fname
            img.save(path, format='JPEG', quality=60)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"image decode error: {e}")
    # Placeholder detection result
    result = {
        "objects": [{"class": "car", "distance_m": 5.2, "confidence": 0.92}],
        "TTC": 2.3,
        "confidence": 0.9,
        "model_version": "v1.0"
    }
    return result

@app.post('/events/create')
async def create_event(payload: dict):
    # store event summary as JSON file (placeholder for DB insertion)
    eid = payload.get('event_id', str(uuid.uuid4()))
    payload['stored_at'] = datetime.datetime.utcnow().isoformat() + 'Z'
    path = EVENTS_DIR / f"{eid}.json"
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return {"status": "ok", "event_id": eid, "path": str(path)}

@app.post('/change_queue/add')
async def add_change(payload: dict):
    cid = str(uuid.uuid4())
    payload_rec = {
        "id": cid,
        "created_at": datetime.datetime.utcnow().isoformat() + 'Z',
        "payload": payload,
        "occurrence_count": payload.get('occurrence_count', 1),
        "accumulated_confidence": payload.get('accumulated_confidence', payload.get('confidence', 0.0)),
        "status": "pending"
    }
    path = CHANGE_DIR / f"{cid}.json"
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(payload_rec, f, ensure_ascii=False, indent=2)
    return {"status": "queued", "change_id": cid}

@app.get('/change_queue/pending')
async def get_pending_changes(limit: int = 100):
    files = sorted(CHANGE_DIR.glob('*.json'))
    res = []
    for p in files[:limit]:
        with open(p, 'r', encoding='utf-8') as f:
            rec = json.load(f)
            res.append(rec)
    return {"count": len(res), "items": res}

@app.post('/tts')
async def tts(payload: dict):
    # very small placeholder: store the text to a file and return path
    text = payload.get('text', '')
    tid = str(uuid.uuid4())
    path = TTS_DIR / f"{tid}.txt"
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    return {"audio_uri": str(path), "tts_id": tid}
