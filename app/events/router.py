from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.database import get_db
from app.models import Event
import json

router = APIRouter()

@router.post('/events/create')
async def create_event(payload: Dict[str, Any], db: Session = Depends(get_db)):
    """
    Stores an event from n8n.
    """
    try:
        # Extract fields from payload
        # n8n sends the whole JSON structure as body
        event_data = Event(
            event_id=payload.get("event_id"),
            user_id=payload.get("user_id"),
            # timestamp_utc might need parsing if passed as string
            timestamp_utc=payload.get("timestamp_utc"),
            trigger_origin=payload.get("trigger_origin"),
            payload_uri=payload.get("payload_uri"),
            features=payload.get("features"),
            decision=payload.get("decision"),
            provenance=payload.get("provenance"),
            storage_policy=payload.get("storage_policy"),
            labeled=payload.get("labeled", False),
            categories=payload.get("categories"),
            meta_data=payload.get("metadata")
        )
        
        db.add(event_data)
        db.commit()
        db.refresh(event_data)
        
        return {"status": "success", "id": event_data.id}
    except Exception as e:
        print(f"Error creating event: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/logs/workflow')
async def log_workflow(payload: Dict[str, Any]):
    """
    Logs workflow execution results.
    """
    # For now, just print to console or append to a file
    print(f"WORKFLOW LOG: {json.dumps(payload)}")
    return {"status": "logged"}
