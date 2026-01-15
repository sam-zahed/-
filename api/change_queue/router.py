from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from app.database import get_db
from app.models import ChangeQueueItem
import datetime

router = APIRouter()

@router.post('/batch_add')
async def batch_add(payload: Dict[str, Any], db: Session = Depends(get_db)):
    """
    Adds candidates to the change queue.
    """
    candidates = payload.get("candidates", [])
    added_count = 0
    
    for candidate in candidates:
        spatial_hash = candidate.get("location", {}).get("spatial_hash")
        if not spatial_hash: continue
        
        # Check existing
        item = db.query(ChangeQueueItem).filter(ChangeQueueItem.spatial_hash == spatial_hash).first()
        
        if item:
            # Update existence
            item.occurrences += 1
            item.last_seen = datetime.datetime.now()
            # Logic to update confidence could be complex, keeping simple for now
            # item.accumulated_confidence = ...
        else:
            item = ChangeQueueItem(
                spatial_hash=spatial_hash,
                status="pending",
                occurrences=1,
                accumulated_confidence=candidate.get("confidence", 0.5),
                last_seen=datetime.datetime.now(),
                candidates_data=[candidate] # Store raw for debug
            )
            db.add(item)
            added_count += 1
            
    db.commit()
    return {"status": "success", "added_count": added_count}

@router.get('/pending')
async def get_pending(min_occurrences: int = 1, min_confidence: float = 0.5, status: str = "pending", db: Session = Depends(get_db)):
    """
    Returns pending changes for n8n processing.
    """
    items = db.query(ChangeQueueItem).filter(
        ChangeQueueItem.status == status,
        ChangeQueueItem.occurrences >= min_occurrences,
        ChangeQueueItem.accumulated_confidence >= min_confidence
    ).all()
    
    # Format for n8n
    changes = []
    for item in items:
        changes.append({
            "spatial_hash": item.spatial_hash,
            "occurrence_count": item.occurrences,
            "accumulated_confidence": item.accumulated_confidence,
            "last_seen_days": (datetime.datetime.now() - item.last_seen.replace(tzinfo=None)).days, # approx
            "hypothesis": {"class": "unknown"} # Should extract from candidates_data
        })
        
    return {"changes": changes}

@router.post('/reject')
async def reject_change(payload: Dict[str, Any], db: Session = Depends(get_db)):
    """
    Marks a change as rejected.
    """
    spatial_hash = payload.get("spatial_hash")
    item = db.query(ChangeQueueItem).filter(ChangeQueueItem.spatial_hash == spatial_hash).first()
    if item:
        item.status = "rejected"
        db.commit()
        return {"status": "rejected"}
    return {"status": "not_found"}
