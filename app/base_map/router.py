from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.database import get_db
from app.models import MapFeature

router = APIRouter()

@router.post('/add_feature')
async def add_feature(payload: Dict[str, Any], db: Session = Depends(get_db)):
    """
    Adds a verified feature to the base map.
    """
    try:
        spatial_hash = payload.get("spatial_hash")
        
        # Check if already exists
        existing = db.query(MapFeature).filter(MapFeature.spatial_hash == spatial_hash).first()
        if existing:
            # Update verify logic or just return
            return {"status": "updated", "id": existing.id}

        feature = MapFeature(
            spatial_hash=spatial_hash,
            feature_class=payload.get("feature_class"),
            location=payload.get("location"),
            confidence=payload.get("confidence"),
            meta_data=payload.get("metadata")
        )
        db.add(feature)
        db.commit()
        
        return {"status": "created", "spatial_hash": spatial_hash}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
