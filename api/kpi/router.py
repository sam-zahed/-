from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
import time

router = APIRouter()

class Event(BaseModel):
    module: str
    metric: str
    value: float
    ts: float = time.time()

DB = []

@router.post('/log')
async def log_event(e: Event):
    DB.append(e.dict())
    return {'status':'ok','count': len(DB)}

@router.get('/metrics')
async def metrics():
    # Return simple aggregations
    by_module = {}
    for ev in DB:
        by_module.setdefault(ev['module'], []).append(ev)
    return {'count': len(DB), 'by_module': {k: len(v) for k,v in by_module.items()}}
