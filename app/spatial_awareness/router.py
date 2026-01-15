"""
API للوعي المكاني - Spatial Awareness Router
يوفر endpoints لنظام المناطق، مسح الغرفة، البيئة الأساسية
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import base64

from .zone_system import zone_system, ZoneSystem
from .stationary_detector import stationary_detector
from .room_scanner import room_scanner
from .environment_baseline import environment_baseline

router = APIRouter()


# ======== Models ========

class ObjectInput(BaseModel):
    """كائن مكتشف"""
    class_name: str  # 'class' is reserved
    class_ar: Optional[str] = None
    distance_m: float
    position: Optional[str] = "front"
    confidence: Optional[float] = 0.5


class AnalyzeRequest(BaseModel):
    """طلب تحليل مع صورتين للمقارنة"""
    image_b64: str
    previous_image_b64: Optional[str] = None


class ZoneClassifyRequest(BaseModel):
    """طلب تصنيف حسب المناطق"""
    objects: List[Dict]


class ScanStartRequest(BaseModel):
    """طلب بدء مسح الغرفة"""
    user_id: str
    room_name: Optional[str] = "غرفة"


class ScanFrameRequest(BaseModel):
    """طلب معالجة frame أثناء المسح"""
    session_id: str
    objects: List[Dict]
    estimated_angle: Optional[float] = None


class LocationRequest(BaseModel):
    """طلب تعيين الموقع"""
    user_id: str
    location_name: str


class BaselineUpdateRequest(BaseModel):
    """طلب تحديث البيئة الأساسية"""
    user_id: str
    location_name: Optional[str] = None
    objects: List[Dict]


class ChangesDetectRequest(BaseModel):
    """طلب اكتشاف التغييرات"""
    user_id: str
    location_name: Optional[str] = None
    current_objects: List[Dict]


# ======== Zone System Endpoints ========

@router.post('/zones/classify')
async def classify_by_zones(request: ZoneClassifyRequest):
    """
    تصنيف الأشياء حسب المناطق (DANGER, WARNING, ATTENTION, AWARENESS, OUTSIDE)
    """
    # تحويل المفاتيح
    objects = []
    for obj in request.objects:
        objects.append({
            'class': obj.get('class') or obj.get('class_name', 'unknown'),
            'class_ar': obj.get('class_ar', obj.get('class', 'unknown')),
            'distance_m': obj.get('distance_m', 999),
            'position': obj.get('position', 'front'),
            'conf': obj.get('confidence') or obj.get('conf', 0.5)
        })
    
    classified = zone_system.classify_by_zone(objects)
    
    # تحويل Enum keys لـ strings
    result = {}
    for zone, objs in classified.items():
        result[zone.value] = objs
    
    return {
        'classified': result,
        'summary': zone_system.get_zone_summary(objects)
    }


@router.post('/zones/filter')
async def filter_alerts_by_zones(request: ZoneClassifyRequest):
    """
    فلترة التنبيهات - فقط الأشياء في المجال الشخصي
    """
    objects = []
    for obj in request.objects:
        objects.append({
            'class': obj.get('class') or obj.get('class_name', 'unknown'),
            'class_ar': obj.get('class_ar', obj.get('class', 'unknown')),
            'distance_m': obj.get('distance_m', 999),
            'position': obj.get('position', 'front'),
            'conf': obj.get('confidence') or obj.get('conf', 0.5)
        })
    
    filtered = zone_system.filter_alerts(objects)
    
    return {
        'alerts': filtered,
        'count': len(filtered),
        'expanded_awareness': zone_system.config.expanded_awareness
    }


@router.post('/zones/expand')
async def expand_awareness():
    """
    توسيع نطاق الوعي (المستخدم يريد معرفة كل شيء حوله)
    """
    result = zone_system.expand_awareness()
    return result


@router.post('/zones/collapse')
async def collapse_awareness():
    """
    تضييق نطاق الوعي (العودة للوضع العادي)
    """
    result = zone_system.collapse_awareness()
    return result


@router.get('/zones/config')
async def get_zone_config():
    """
    الحصول على إعدادات المناطق الحالية
    """
    return {
        'danger_radius': zone_system.config.danger_radius,
        'warning_radius': zone_system.config.warning_radius,
        'attention_radius': zone_system.config.attention_radius,
        'awareness_radius': zone_system.config.awareness_radius,
        'alert_outside_zone': zone_system.config.alert_outside_zone,
        'expanded_awareness': zone_system.config.expanded_awareness
    }


# ======== Stationary Detection Endpoints ========

@router.post('/motion/analyze')
async def analyze_motion(request: AnalyzeRequest):
    """
    تحليل حالة الحركة - هل المستخدم ثابت أم متحرك؟
    """
    try:
        # فك تشفير الصورة
        if "," in request.image_b64:
            header, encoded = request.image_b64.split(",", 1)
        else:
            encoded = request.image_b64
        
        image_bytes = base64.b64decode(encoded)
        
        # تحليل الحركة
        state = stationary_detector.analyze_frame(image_bytes)
        
        return stationary_detector.get_status()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/motion/status')
async def get_motion_status():
    """
    الحصول على حالة الحركة الحالية
    """
    return stationary_detector.get_status()


@router.post('/motion/reset')
async def reset_motion_detector():
    """
    إعادة تعيين كاشف الحركة
    """
    stationary_detector.reset()
    return {'message': 'تم إعادة تعيين كاشف الحركة', 'success': True}


# ======== Room Scanning Endpoints ========

@router.post('/scan/start')
async def start_room_scan(request: ScanStartRequest):
    """
    بدء مسح الغرفة 360 درجة
    """
    result = room_scanner.start_scan(request.user_id, request.room_name)
    return result


@router.post('/scan/frame')
async def process_scan_frame(request: ScanFrameRequest):
    """
    معالجة frame أثناء المسح
    """
    result = room_scanner.process_scan_frame(
        request.session_id,
        request.objects,
        request.estimated_angle
    )
    return result


@router.get('/scan/status/{session_id}')
async def get_scan_status(session_id: str):
    """
    الحصول على حالة جلسة المسح
    """
    return room_scanner.get_session_status(session_id)


@router.post('/scan/cancel/{session_id}')
async def cancel_scan(session_id: str):
    """
    إلغاء جلسة المسح
    """
    return room_scanner.cancel_scan(session_id)


@router.get('/scan/rooms/{user_id}')
async def get_saved_rooms(user_id: str):
    """
    قائمة الغرف المحفوظة للمستخدم
    """
    rooms = room_scanner.get_saved_rooms(user_id)
    return {'rooms': rooms, 'count': len(rooms)}


# ======== Environment Baseline Endpoints ========

@router.post('/baseline/location')
async def set_location(request: LocationRequest):
    """
    تعيين الموقع الحالي للمستخدم
    """
    # تحديث المستخدم في environment_baseline
    environment_baseline.user_id = request.user_id
    result = environment_baseline.set_location(request.location_name)
    return result


@router.post('/baseline/update')
async def update_baseline(request: BaselineUpdateRequest):
    """
    تحديث البيئة الأساسية بالأشياء المكتشفة
    """
    environment_baseline.user_id = request.user_id
    result = environment_baseline.update_baseline(request.objects, request.location_name)
    return result


@router.post('/baseline/changes')
async def detect_changes(request: ChangesDetectRequest):
    """
    اكتشاف التغييرات في البيئة
    """
    environment_baseline.user_id = request.user_id
    result = environment_baseline.detect_changes(request.current_objects, request.location_name)
    return result


@router.get('/baseline/summary')
async def get_baseline_summary(user_id: str, location_name: Optional[str] = None):
    """
    ملخص البيئة الأساسية
    """
    environment_baseline.user_id = user_id
    if location_name:
        environment_baseline.set_location(location_name)
    return environment_baseline.get_baseline_summary(location_name)
