"""
PHASE 4: تحليل متقدم مع جميع التحسينات
يتضمن:
- Caching
- Personalization 
- Dynamic alerts
- Ambient sound analysis
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List, Dict
import time

from .router import router, learning_system, context_manager, alert_manager
from app.vision.model import detector
from app.utils.caching import cache_manager, perf_monitor, timed
from app.utils.advanced_features import (
    ambient_sound_detector, dynamic_alert_system, location_awareness
)
from app.audio.transcribe import transcribe_audio_bytes
import base64

class AdvancedAnalysisRequest(BaseModel):
    """طلب تحليل متقدم"""
    image_b64: str
    audio_b64: Optional[str] = None
    user_id: str = "default"
    enable_sound_analysis: bool = True
    enable_dynamic_alerts: bool = True

class AdvancedAnalysisResponse(BaseModel):
    """رد التحليل المتقدم"""
    objects: List[Dict]
    ambient_sounds: Dict = {}
    dynamic_alerts: List[Dict] = []
    location_inference: Optional[str] = None
    personalization_adjustments: Dict = {}
    performance_stats: Dict = {}

@router.post('/advanced_analyze', response_model=AdvancedAnalysisResponse)
@timed("advanced_analyze")
async def advanced_scene_analysis(request: AdvancedAnalysisRequest):
    """
    PHASE 4: تحليل متقدم للمشهد
    يتضمن جميع التحسينات الأربعة
    """
    
    start_time = time.time()
    
    # ============ PHASE 2: Check Cache ============
    image_bytes = base64.b64decode(request.image_b64.split(',')[1] if ',' in request.image_b64 else request.image_b64)
    cached_result = cache_manager.get(image_bytes, prefix='advanced_analyze')
    
    if cached_result:
        return cached_result
    
    # ============ PHASE 1: Detect Objects ============
    objects = detector.detect(image_bytes)
    
    # ============ PHASE 4.2: Dynamic Alerts ============
    dynamic_alerts = []
    if request.enable_dynamic_alerts:
        for obj in objects:
            # تتبع الكائن وحدد ما إذا كان يقترب
            alert = dynamic_alert_system.track_object(
                obj['class'],
                obj['distance_m']
            )
            
            if alert and alert.urgency_level >= 3:
                dynamic_alerts.append({
                    'object': obj['class'],
                    'object_ar': obj['class_ar'],
                    'distance': alert.distance,
                    'trend': alert.distance_trend,
                    'urgency': alert.urgency_level,
                    'recommendation': alert.recommendation
                })
    
    # ============ PHASE 4.1: Analyze Ambient Sounds ============
    ambient_sounds = {}
    location_inference = None
    if request.enable_sound_analysis and request.audio_b64:
        try:
            audio_bytes = base64.b64decode(
                request.audio_b64.split(',')[1] 
                if ',' in request.audio_b64 
                else request.audio_b64
            )
            
            ambient_sounds = ambient_sound_detector.analyze_audio(audio_bytes)
            location_inference = ambient_sound_detector.infer_location(ambient_sounds)
        except:
            pass
    
    # ============ PHASE 3: Apply Personalization ============
    personalization_adjustments = {}
    if request.user_id != "default":
        learning_system.user_id = request.user_id
        learning_system.profile = learning_system._load_profile()
    
    # اضبط الكائنات بناءً على التفضيلات الشخصية
    filtered_objects = []
    for obj in objects:
        # تحقق ما إذا كان يجب تنبيه المستخدم
        if not learning_system.should_alert_about(obj['class']):
            personalization_adjustments[obj['class']] = 'filtered_out'
            continue
        
        # اضبط الأولوية
        priority_adj = learning_system.get_personalized_priority_adjustment(obj['class'])
        if priority_adj != 0:
            personalization_adjustments[obj['class']] = {
                'adjustment': priority_adj,
                'original_distance': obj['distance_m']
            }
        
        filtered_objects.append(obj)
    
    # سجل التفاعل للتعلم
    for obj in filtered_objects[:3]:  # الأجسام الثلاثة الأقرب
        learning_system.record_interaction(
            obj['class'],
            action='attended',
            duration=None
        )
    
    # ============ PHASE 4.3: Location Awareness ============
    location_info = {}
    if location_inference:
        location_info = {
            'inferred_location': location_inference,
            'expected_hazards': {
                'street': ['cars', 'bicycles', 'pedestrians'],
                'park': ['irregular terrain', 'water'],
                'home': ['stairs', 'furniture']
            }.get(location_inference, [])
        }
    
    # ============ Performance Stats ============
    elapsed = time.time() - start_time
    stats = perf_monitor.get_stats()
    
    response = AdvancedAnalysisResponse(
        objects=filtered_objects[:5],  # أعد أقرب 5 أجسام
        ambient_sounds=ambient_sounds,
        dynamic_alerts=dynamic_alerts,
        location_inference=location_inference,
        personalization_adjustments=personalization_adjustments,
        performance_stats={
            'total_time_ms': elapsed * 1000,
            'object_detection_avg_ms': stats.get('detect', {}).get('avg', 0) * 1000,
            'cache_hit': cached_result is not None,
            'learning_stats': learning_system.get_learning_statistics()
        }
    )
    
    # ============ PHASE 2: Cache Result ============
    cache_manager.set(image_bytes, response.dict(), prefix='advanced_analyze')
    
    return response

# أضف إلى الـ router الرئيسي
# router.post('/advanced_analyze')(advanced_scene_analysis)
