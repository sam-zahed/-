from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from .vision.router import router as vision_router
from .audio.router import router as audio_router
from .device_link.router import router as device_router
from .kpi.router import router as kpi_router

# New routers
from .infer.router import router as infer_router
from .events.router import router as events_router
from app.change_queue.router import router as change_queue_router
from .base_map.router import router as base_map_router
from .notifications.router import router as notifications_router
from app.labeling.router import router as labeling_router
from app.navigation.router import router as navigation_router
from .proxy.router import router as proxy_router
from app.interactive.router import router as interactive_router
from app.ocr.router import router as ocr_router

# Advanced Features - Spatial Awareness & Learning
from app.spatial_awareness.router import router as spatial_awareness_router
from app.learning.router import router as learning_router

# Smart Conversational Assistant
from app.assistant.router import router as assistant_router

from .database import engine, Base

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Smart Glasses Agent - Conversational AI Assistant")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers
app.include_router(vision_router, prefix="/vision", tags=["vision"])
app.include_router(audio_router, prefix="/audio", tags=["audio"])
app.include_router(device_router, prefix="/device", tags=["device_link"])
app.include_router(events_router, prefix="", tags=["events"])
app.include_router(change_queue_router, prefix="/change_queue", tags=["change_queue"])
app.include_router(labeling_router, prefix="", tags=["labeling"])
app.include_router(interactive_router, prefix="/device") # Handles own paths
app.include_router(ocr_router, prefix="/ocr", tags=["ocr"])
app.include_router(kpi_router, prefix="/kpi", tags=["kpi"])
app.include_router(infer_router, prefix="/infer", tags=["infer"])
app.include_router(base_map_router, prefix="/base_map", tags=["base_map"])
app.include_router(notifications_router, prefix="/notifications", tags=["notifications"])
app.include_router(proxy_router, prefix="/proxy", tags=["proxy"])
app.include_router(navigation_router, prefix="/navigation", tags=["navigation"])

# Advanced Blind Assistance Features
app.include_router(spatial_awareness_router, prefix="/spatial", tags=["spatial_awareness"])
app.include_router(learning_router, prefix="/learning", tags=["learning"])

# Smart Conversational Assistant (Main Entry Point)
app.include_router(assistant_router, prefix="/assistant", tags=["assistant"])

# Static Files (Client)
# Ensure client dir exists to avoid error if missing
client_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "client")
if not os.path.exists(client_path):
    os.makedirs(client_path)

app.mount("/client", StaticFiles(directory=client_path, html=True), name="client")

@app.get('/')
async def root():
    return {
        "status": "ok", 
        "message": "مساعد المكفوفين الذكي - Smart Blind Assistant",
        "assistant_endpoint": "/assistant/chat",
        "docs": "/docs",
        "modules": [
            "assistant", "vision", "audio", "navigation", 
            "spatial_awareness", "learning"
        ],
        "assistant_commands": [
            "ماذا أمامي؟ - وصف المشهد",
            "أين الباب؟ - البحث عن شيء",
            "اقرأ - قراءة النصوص",
            "اسكت - وضع الصمت",
            "دور حولي - مسح كامل"
        ]
    }


