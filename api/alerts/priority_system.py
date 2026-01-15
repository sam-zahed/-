from enum import Enum
from typing import List, Dict, Optional
import asyncio

class AlertPriority(Enum):
    CRITICAL = 1    # خطر فوري (درج، حفرة، سيارة قريبة)
    HIGH = 2        # تحذير مهم (شخص قريب، باب)
    MEDIUM = 3      # معلومة مفيدة (أثاث، أشياء)
    LOW = 4         # معلومة عامة (ألوان، تفاصيل)

PRIORITY_MAP = {
    # أخطار فورية
    'stairs': AlertPriority.CRITICAL,
    'staircase': AlertPriority.CRITICAL,
    'steps': AlertPriority.CRITICAL,
    'hole': AlertPriority.CRITICAL,
    'hole in ground': AlertPriority.CRITICAL,
    'pothole': AlertPriority.CRITICAL,
    'escalator': AlertPriority.CRITICAL,
    
    # تحذيرات عالية
    'car': AlertPriority.HIGH,
    'truck': AlertPriority.HIGH,
    'bus': AlertPriority.HIGH,
    'motorcycle': AlertPriority.HIGH,
    'bicycle': AlertPriority.HIGH,
    'door': AlertPriority.HIGH,
    'open door': AlertPriority.HIGH,
    'child': AlertPriority.HIGH,  # طفل = أولوية عالية
    
    # متوسطة
    'person': AlertPriority.MEDIUM,
    'man': AlertPriority.MEDIUM,
    'woman': AlertPriority.MEDIUM,
    'wall': AlertPriority.MEDIUM,
    'obstacle': AlertPriority.MEDIUM,
    'corner': AlertPriority.MEDIUM,
    
    # منخفضة
    'chair': AlertPriority.LOW,
    'table': AlertPriority.LOW,
    'couch': AlertPriority.LOW,
    'bed': AlertPriority.LOW,
}

DISTANCE_MULTIPLIER = {
    # كلما كان الشيء أقرب، زادت الأولوية
    0.5: 3,   # أقل من نصف متر = ضاعف الأولوية 3 مرات
    1.0: 2,   # أقل من متر = ضاعف مرتين
    2.0: 1.5, # أقل من مترين = ضاعف 1.5
    5.0: 1,   # أكثر من 5 أمتار = عادي
}

ARABIC_ALERTS = {
    AlertPriority.CRITICAL: "تحذير خطر!",
    AlertPriority.HIGH: "انتبه!",
    AlertPriority.MEDIUM: "ملاحظة:",
    AlertPriority.LOW: ""
}

DIRECTION_AR = {
    'front': 'أمامك',
    'left': 'على يسارك',
    'right': 'على يمينك',
    'back': 'خلفك',
    'center': 'في المنتصف'
}

def calculate_direction(bbox: List[float], image_width: int = 640) -> str:
    """حساب اتجاه الشيء بناءً على موقعه في الصورة"""
    center_x = (bbox[0] + bbox[2]) / 2
    
    # تقسيم الصورة لثلاث مناطق
    left_boundary = image_width * 0.35
    right_boundary = image_width * 0.65
    
    if center_x < left_boundary:
        return 'left'
    elif center_x > right_boundary:
        return 'right'
    else:
        return 'front'

def get_alert_priority(obj_class: str, distance: float) -> int:
    """حساب أولوية التنبيه بناءً على نوع الشيء والمسافة"""
    base_priority = PRIORITY_MAP.get(obj_class, AlertPriority.LOW)
    
    # تعديل حسب المسافة
    for dist_threshold, multiplier in sorted(DISTANCE_MULTIPLIER.items()):
        if distance <= dist_threshold:
            priority_value = base_priority.value / multiplier
            return max(1, int(priority_value))
    
    return base_priority.value

def generate_alert_message(detection: Dict, image_width: int = 640) -> Dict:
    """توليد رسالة تنبيه ذكية"""
    obj_class = detection.get('class', 'unknown')
    class_ar = detection.get('class_ar', obj_class)
    distance = detection.get('distance_m', 5.0)
    bbox = detection.get('bbox', [0, 0, image_width, 480])
    confidence = detection.get('conf', 0.0)
    
    priority_level = get_alert_priority(obj_class, distance)
    priority = AlertPriority(priority_level)
    
    direction = calculate_direction(bbox, image_width)
    direction_ar = DIRECTION_AR[direction]
    
    alert_prefix = ARABIC_ALERTS[priority]
    
    # صياغة الرسالة حسب المسافة
    if distance < 0.5:
        distance_text = f"قريب جداً منك"
    elif distance < 1:
        distance_text = f"على بعد أقل من متر {direction_ar}"
    elif distance < 2:
        distance_text = f"على بعد متر واحد {direction_ar}"
    elif distance < 3:
        distance_text = f"على بعد مترين {direction_ar}"
    else:
        distance_text = f"على بعد {int(distance)} متر {direction_ar}"
    
    # بناء الرسالة الكاملة
    if priority == AlertPriority.CRITICAL:
        message = f"{alert_prefix} {class_ar} {distance_text}!"
    elif priority == AlertPriority.HIGH:
        message = f"{alert_prefix} {class_ar} {distance_text}"
    else:
        message = f"{class_ar} {distance_text}"
    
    return {
        'priority': priority.value,
        'priority_name': priority.name,
        'message': message,
        'object': class_ar,
        'object_en': obj_class,
        'distance': distance,
        'direction': direction,
        'direction_ar': direction_ar,
        'confidence': confidence,
        'should_speak': priority.value <= 2,  # فقط CRITICAL و HIGH
        'urgency': 'critical' if priority == AlertPriority.CRITICAL else 
                   'high' if priority == AlertPriority.HIGH else
                   'medium' if priority == AlertPriority.MEDIUM else 'low'
    }

async def process_detections_with_alerts(detections: List[Dict], image_width: int = 640) -> Dict:
    """معالجة الكشوفات وتوليد التنبيهات المرتبة"""
    if not detections:
        return {
            'all_alerts': [],
            'critical_alerts': [],
            'speak_message': '',
            'has_danger': False,
            'object_count': 0
        }
    
    alerts = []
    
    for detection in detections:
        alert = generate_alert_message(detection, image_width)
        alerts.append(alert)
    
    # ترتيب حسب الأولوية ثم المسافة
    alerts.sort(key=lambda x: (x['priority'], x['distance']))
    
    # التنبيهات الحرجة والعالية فقط
    critical_alerts = [a for a in alerts if a['should_speak']]
    
    # بناء الرسالة الصوتية (أهم 3 فقط لتجنب الإطالة)
    speak_parts = []
    for alert in critical_alerts[:3]:
        speak_parts.append(alert['message'])
    
    speak_message = '. '.join(speak_parts)
    
    # كشف الخطر
    has_danger = any(a['priority'] == 1 for a in alerts)
    
    return {
        'all_alerts': alerts,
        'critical_alerts': critical_alerts,
        'speak_message': speak_message,
        'has_danger': has_danger,
        'object_count': len(detections),
        'closest_object': alerts[0] if alerts else None
    }

def get_summary_message(alerts_data: Dict) -> str:
    """توليد رسالة ملخصة عن المشهد"""
    if not alerts_data['all_alerts']:
        return "لا يوجد أشياء مكتشفة"
    
    count = alerts_data['object_count']
    closest = alerts_data['closest_object']
    
    if alerts_data['has_danger']:
        return f"تحذير! {closest['object']} على بعد {closest['distance']:.1f} متر"
    elif count == 1:
        return f"{closest['object']} {closest['direction_ar']}"
    elif count <= 3:
        objects = [a['object'] for a in alerts_data['all_alerts'][:3]]
        return f"يوجد {', '.join(objects)}"
    else:
        return f"يوجد {count} أشياء، أقربها {closest['object']}"
