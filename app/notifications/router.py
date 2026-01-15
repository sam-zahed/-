from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter()

@router.post('/send')
async def send_notification(payload: Dict[str, Any]):
    """
    Mock send notification.
    """
    print(f"NOTIFICATION SENT: {payload}")
    return {"status": "sent"}

@router.post('/send_to_labelers')
async def send_to_labelers(payload: Dict[str, Any]):
    """
    Mock send to labelers.
    """
    print(f"LABELER NOTIFICATION: {payload}")
    return {"status": "sent", "recipient_count": 5}
