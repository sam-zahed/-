from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.database import get_db
from app.models import LabelingBatch, LabelingTask, Event
import datetime

router = APIRouter()

@router.get('/labeling_queue/top_k')
async def get_top_k(k: int = 10, criteria: str = "uncertainty", db: Session = Depends(get_db)):
    """
    Returns top-k uncertain samples from Events table.
    """
    # Query real events that are not labeled
    # For MVP, just get latest events. Ideally filter by uncertainty.
    events = db.query(Event).filter(Event.labeled == False).order_by(Event.created_at.desc()).limit(k).all()
    
    samples = []
    for event in events:
        # Extract confidence
        feats = event.features or {}
        # Calculate uncertainty logic here if needed, or let n8n do it
        
        samples.append({
            "event_id": event.event_id,
            "payload_uri": event.payload_uri,
            "features": feats,
            "timestamp_utc": event.timestamp_utc.isoformat() if event.timestamp_utc else None,
            "metadata": event.meta_data,
            # Flag for active learning
            "active_learning_candidate": True 
        })
    
    return {"samples": samples}

@router.post('/create_batch')
async def create_batch(payload: Dict[str, Any], db: Session = Depends(get_db)):
    """
    Creates a labeling batch.
    """
    try:
        json_body = payload.get("json", {}) # n8n structure might vary
        
        batch = LabelingBatch(
            batch_id=f"batch_{datetime.datetime.now().timestamp()}",
            task_count=1, # Mock
            status="created"
        )
        db.add(batch)
        db.commit()
        
        return {
            "batch_id": batch.batch_id,
            "status": "created"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
