"""
API endpoints لإدارة المسارات والمشي المستقيم
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
import base64

from .routes_manager import route_manager
from .straight_walk import straight_walk_guide

router = APIRouter()

class RouteCreate(BaseModel):
    name: str
    description: Optional[str] = ""

class LandmarkAdd(BaseModel):
    route_name: str
    object: str
    object_ar: str
    position: str
    distance: float

class WarningAdd(BaseModel):
    route_name: str
    warning: str

class StraightWalkAnalyze(BaseModel):
    image_b64: str

class StraightWalkSettings(BaseModel):
    threshold: Optional[float] = None
    cooldown: Optional[float] = None

@router.post('/routes/create')
async def create_route(route: RouteCreate):
    """إنشاء مسار جديد"""
    success = route_manager.add_route(route.name, route.description)
    if success:
        return {'message': f'تم إنشاء المسار: {route.name}', 'success': True}
    return {'message': 'المسار موجود بالفعل', 'success': False}

@router.get('/routes/list')
async def list_routes():
    """قائمة جميع المسارات المحفوظة"""
    routes = route_manager.list_routes()
    return {'routes': routes, 'count': len(routes)}

@router.post('/routes/start/{route_name}')
async def start_route(route_name: str):
    """بدء مسار محفوظ"""
    route = route_manager.start_route(route_name)
    if route:
        return {
            'message': f'بدأ المسار: {route_name}',
            'route': route,
            'success': True
        }
    raise HTTPException(status_code=404, detail='المسار غير موجود')

@router.post('/routes/landmark')
async def add_landmark(landmark: LandmarkAdd):
    """إضافة علامة مميزة للمسار"""
    route_manager.add_landmark(landmark.route_name, landmark.dict())
    return {'message': 'تم إضافة العلامة', 'success': True}

@router.post('/routes/warning')
async def add_warning(warning: WarningAdd):
    """إضافة تحذير للمسار"""
    route_manager.add_warning(warning.route_name, warning.warning)
    return {'message': 'تم إضافة التحذير', 'success': True}

@router.get('/routes/guidance/{route_name}')
async def get_guidance(route_name: str, current_objects: str):
    """الحصول على إرشادات للمسار"""
    import json
    objects = json.loads(current_objects)
    guidance = route_manager.get_route_guidance(route_name, objects)
    return {'guidance': guidance}


# ======== Straight Walking Endpoints ========

@router.post('/straight/start')
async def start_straight_tracking(request: Optional[StraightWalkAnalyze] = None):
    """
    بدء تتبع المشي المستقيم
    يمكن إرسال صورة أولية للمعايرة
    """
    initial_bytes = None
    if request and request.image_b64:
        if "," in request.image_b64:
            _, encoded = request.image_b64.split(",", 1)
        else:
            encoded = request.image_b64
        initial_bytes = base64.b64decode(encoded)
    
    result = straight_walk_guide.start_tracking(initial_bytes)
    return result

@router.post('/straight/stop')
async def stop_straight_tracking():
    """إيقاف تتبع المشي المستقيم"""
    return straight_walk_guide.stop_tracking()

@router.post('/straight/analyze')
async def analyze_deviation(request: StraightWalkAnalyze):
    """
    تحليل الانحراف عن المسار المستقيم
    """
    try:
        if "," in request.image_b64:
            _, encoded = request.image_b64.split(",", 1)
        else:
            encoded = request.image_b64
        
        image_bytes = base64.b64decode(encoded)
        state = straight_walk_guide.analyze_deviation(image_bytes)
        
        return {
            'deviation': state.deviation,
            'deviation_amount': round(state.deviation_amount, 3),
            'should_alert': state.should_alert,
            'alert_message': state.alert_message,
            'confidence': round(state.confidence, 2)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/straight/calibrate')
async def calibrate_path(request: StraightWalkAnalyze):
    """معايرة مسار المشي من الصورة الحالية"""
    try:
        if "," in request.image_b64:
            _, encoded = request.image_b64.split(",", 1)
        else:
            encoded = request.image_b64
        
        image_bytes = base64.b64decode(encoded)
        result = straight_walk_guide.calibrate_path(image_bytes)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/straight/status')
async def get_straight_status():
    """حالة تتبع المشي المستقيم"""
    return straight_walk_guide.get_status()

@router.post('/straight/settings')
async def update_straight_settings(settings: StraightWalkSettings):
    """تحديث إعدادات المشي المستقيم"""
    return straight_walk_guide.update_settings(
        threshold=settings.threshold,
        cooldown=settings.cooldown
    )

@router.post('/straight/reset')
async def reset_straight_walk():
    """إعادة تعيين نظام المشي المستقيم"""
    straight_walk_guide.reset()
    return {'message': 'تم إعادة تعيين نظام المشي المستقيم', 'success': True}

