from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any
import httpx
import os

router = APIRouter()

N8N_WEBHOOK_URL = os.environ.get("N8N_WEBHOOK_URL", "http://n8n:5678/webhook/ingest")

@router.post('/ingest')
async def proxy_ingest(payload: Dict[str, Any]):
    """
    Forwards the ingest request to n8n webhook avoids CORS issues on the client.
    """
    async with httpx.AsyncClient() as client:
        try:
            print(f"Proxying to n8n: {N8N_WEBHOOK_URL}")
            # We forward to the internal n8n service name
            response = await client.post(
                N8N_WEBHOOK_URL,
                json=payload,
                timeout=30.0
            )
            
            print(f"n8n Response Status: {response.status_code}")
            print(f"n8n Response Body: {response.text[:200]}...") # Print first 200 chars

            if response.status_code >= 400:
                 # If n8n errors, tries to return the detail
                 print(f"n8n ERROR: {response.text}")
                 return {"status": "error", "n8n_response": response.text}
                 
            return response.json()
            
        except httpx.RequestError as exc:
            print(f"An error occurred while requesting {exc.request.url!r}.")
            raise HTTPException(status_code=502, detail="Could not connect to n8n workflow service")
