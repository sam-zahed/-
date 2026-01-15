"""
Smart Blind Assistant - Main FastAPI Application
AI-powered assistance system for blind individuals
Dansk support / Danish support

Main endpoints:
- /assistant/* - Chat, commands, and voice interaction
- /vision/* - Object detection, OCR, depth estimation
- /audio/* - Speech recognition and synthesis
- /navigation/* - Route management and spatial guidance
- /client/ - Web interface for voice interaction
"""

from fastapi import FastAPI, StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import os

# Import all routers
from .assistant.router import router as assistant_router
from .vision.router import router as vision_router
from .audio.router import router as audio_router
from .navigation.router import router as navigation_router
from .infer.router import router as infer_router
from .events.router import router as events_router
from .change_queue.router import router as change_queue_router
from .labeling.router import router as labeling_router
from .notifications.router import router as notifications_router
from .kpi.router import router as kpi_router
from .ocr.router import router as ocr_router
from .proxy.router import router as proxy_router
from .learning.router import router as learning_router
from .spatial_awareness.router import router as spatial_router
from .device_link.router import router as device_router
from .interactive.router import router as interactive_router
from .base_map.router import router as base_map_router

# Create FastAPI application
app = FastAPI(
    title="Smart Blind Assistant API",
    description="AI-powered assistance system for blind individuals with voice interaction",
    version="1.0.0"
)

# === CORS Configuration ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Include Routers ===
app.include_router(assistant_router, prefix="/assistant", tags=["Assistant"])
app.include_router(vision_router, prefix="/vision", tags=["Vision"])
app.include_router(audio_router, prefix="/audio", tags=["Audio"])
app.include_router(navigation_router, prefix="/navigation", tags=["Navigation"])
app.include_router(infer_router, prefix="/infer", tags=["Inference"])
app.include_router(events_router, prefix="/events", tags=["Events"])
app.include_router(change_queue_router, prefix="/change_queue", tags=["Change Queue"])
app.include_router(labeling_router, prefix="/labeling", tags=["Labeling"])
app.include_router(notifications_router, prefix="/notifications", tags=["Notifications"])
app.include_router(kpi_router, prefix="/kpi", tags=["KPI"])
app.include_router(ocr_router, prefix="/ocr", tags=["OCR"])
app.include_router(proxy_router, prefix="/proxy", tags=["Proxy"])
app.include_router(learning_router, prefix="/learning", tags=["Learning"])
app.include_router(spatial_router, prefix="/spatial", tags=["Spatial Awareness"])
app.include_router(device_router, prefix="/device", tags=["Device Link"])
app.include_router(interactive_router, prefix="/interactive", tags=["Interactive"])
app.include_router(base_map_router, prefix="/base_map", tags=["Base Map"])

# === Static Files ===
client_path = os.path.join(os.path.dirname(__file__), '..', 'client')
if os.path.exists(client_path):
    app.mount("/client", StaticFiles(directory=client_path, html=True), name="client")

# === Root Endpoint ===
@app.get("/", tags=["Health"])
async def root():
    """Health check and API information"""
    return {
        "status": "ok",
        "message": "Smart Blind Assistant API",
        "version": "1.0.0",
        "documentation": "/docs",
        "interface": "/client/",
        "languages": ["ar", "en", "da"]
    }

@app.get("/health", tags=["Health"])
async def health():
    """Health check endpoint for monitoring"""
    return {"status": "healthy", "service": "smart-blind-assistant"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
