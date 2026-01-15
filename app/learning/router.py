"""
API للتعلم التكيفي - Learning Router
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional

from .adaptive_system import adaptive_learning, AdaptiveLearning

router = APIRouter()


# ======== Models ========

class InteractionRecord(BaseModel):
    """تسجيل تفاعل"""
    event_type: str  # alert_shown, alert_ignored, object_query
    object_class: str
    user_response: str  # acknowledged, ignored, asked_more
    metadata: Optional[Dict] = None


class SettingsUpdate(BaseModel):
    """تحديث الإعدادات"""
    intensity: Optional[str] = None  # low, medium, high
    language: Optional[str] = None   # ar, en, da
    voice_speed: Optional[float] = None


class FilterRequest(BaseModel):
    """طلب فلترة حسب التفضيلات"""
    user_id: Optional[str] = "default"
    objects: List[Dict]


# ======== Endpoints ========

@router.post('/interaction')
async def record_interaction(record: InteractionRecord, user_id: str = "default"):
    """
    تسجيل تفاعل المستخدم للتعلم منه
    """
    adaptive_learning.user_id = user_id
    adaptive_learning.record_interaction(
        event_type=record.event_type,
        object_class=record.object_class,
        user_response=record.user_response,
        metadata=record.metadata
    )
    
    return {
        'message': 'تم تسجيل التفاعل',
        'success': True
    }


@router.post('/filter')
async def filter_by_preferences(request: FilterRequest):
    """
    فلترة الكائنات حسب تفضيلات المستخدم
    """
    if request.user_id:
        adaptive_learning.user_id = request.user_id
    
    filtered = adaptive_learning.filter_by_preferences(request.objects)
    
    return {
        'objects': filtered,
        'original_count': len(request.objects),
        'filtered_count': len(filtered)
    }


@router.get('/priority/{object_class}')
async def get_priority(object_class: str, user_id: str = "default"):
    """
    الحصول على الأولوية المخصصة لنوع كائن
    """
    adaptive_learning.user_id = user_id
    
    priority = adaptive_learning.get_personalized_priority({
        'class': object_class,
        'priority': 3  # أولوية افتراضية
    })
    
    return {
        'object_class': object_class,
        'personalized_priority': priority
    }


@router.get('/summary')
async def get_user_summary(user_id: str = "default"):
    """
    ملخص ملف تعريف المستخدم
    """
    adaptive_learning.user_id = user_id
    return adaptive_learning.get_user_summary()


@router.post('/settings')
async def update_settings(settings: SettingsUpdate, user_id: str = "default"):
    """
    تحديث إعدادات المستخدم
    """
    adaptive_learning.user_id = user_id
    return adaptive_learning.update_settings(
        intensity=settings.intensity,
        language=settings.language,
        voice_speed=settings.voice_speed
    )


@router.post('/reset')
async def reset_preferences(user_id: str = "default", object_class: Optional[str] = None):
    """
    إعادة تعيين التفضيلات
    """
    adaptive_learning.user_id = user_id
    return adaptive_learning.reset_preferences(object_class)


@router.get('/session')
async def export_session_data(user_id: str = "default"):
    """
    تصدير بيانات الجلسة
    """
    adaptive_learning.user_id = user_id
    return adaptive_learning.export_session_data()
