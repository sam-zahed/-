"""
نظام المناطق الشخصية - Personal Zone System
مثل أنظمة السيارات الذكية للمساعدة في الوعي المكاني

هذا النظام يقسم المحيط إلى مناطق ويتعامل مع كل منطقة بطريقة مختلفة:
- DANGER: أقل من 0.5 متر - خطر فوري
- WARNING: 0.5 - 1.5 متر - تحذير
- ATTENTION: 1.5 - 3 متر - انتباه
- AWARENESS: 3 - 6 متر - وعي عام
- OUTSIDE: أكثر من 6 متر - خارج المجال (لا ينبه إلا بطلب)
"""

from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path


class Zone(Enum):
    """مناطق الوعي المكاني"""
    DANGER = "danger"       # خطر فوري
    WARNING = "warning"     # تحذير
    ATTENTION = "attention" # انتباه
    AWARENESS = "awareness" # وعي عام
    OUTSIDE = "outside"     # خارج المجال


# حدود المناطق بالأمتار
ZONE_THRESHOLDS = {
    Zone.DANGER: 0.5,
    Zone.WARNING: 1.5,
    Zone.ATTENTION: 3.0,
    Zone.AWARENESS: 6.0,
    Zone.OUTSIDE: float('inf')
}

# رسائل المناطق بالعربية
ZONE_MESSAGES_AR = {
    Zone.DANGER: "تحذير خطر!",
    Zone.WARNING: "انتبه!",
    Zone.ATTENTION: "يوجد",
    Zone.AWARENESS: "",
    Zone.OUTSIDE: ""
}

# أولوية التنبيه لكل منطقة (1 = أعلى)
ZONE_PRIORITY = {
    Zone.DANGER: 1,
    Zone.WARNING: 2,
    Zone.ATTENTION: 3,
    Zone.AWARENESS: 4,
    Zone.OUTSIDE: 5
}


@dataclass
class ZoneConfig:
    """إعدادات نظام المناطق القابلة للتخصيص"""
    danger_radius: float = 0.5
    warning_radius: float = 1.5
    attention_radius: float = 3.0
    awareness_radius: float = 6.0
    
    # هل ينبه للأشياء خارج المجال تلقائياً؟
    alert_outside_zone: bool = False
    
    # هل المستخدم طلب مسح كامل (توسيع الوعي)؟
    expanded_awareness: bool = False
    
    # الوقت الأخير للتوسيع (للتراجع التلقائي)
    expansion_time: Optional[datetime] = None
    
    # مدة التوسيع بالثواني (بعدها يرجع عادي)
    expansion_duration: int = 30


class ZoneSystem:
    """
    نظام المناطق الشخصية للوعي المكاني
    يعمل مثل أنظمة مساعدة القيادة في السيارات
    """
    
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self.config = ZoneConfig()
        self.config_file = Path(__file__).parent.parent / 'data' / 'zones' / f'{user_id}_config.json'
        self.load_config()
        
    def load_config(self):
        """تحميل إعدادات المستخدم"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.config = ZoneConfig(**{k: v for k, v in data.items() 
                                                if k in ZoneConfig.__dataclass_fields__})
            except Exception as e:
                print(f"⚠️ Error loading zone config: {e}")
    
    def save_config(self):
        """حفظ إعدادات المستخدم"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                config_dict = {
                    'danger_radius': self.config.danger_radius,
                    'warning_radius': self.config.warning_radius,
                    'attention_radius': self.config.attention_radius,
                    'awareness_radius': self.config.awareness_radius,
                    'alert_outside_zone': self.config.alert_outside_zone,
                    'expanded_awareness': self.config.expanded_awareness,
                    'expansion_duration': self.config.expansion_duration
                }
                json.dump(config_dict, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving zone config: {e}")
    
    def get_zone(self, distance: float) -> Zone:
        """تحديد المنطقة بناءً على المسافة"""
        if distance <= self.config.danger_radius:
            return Zone.DANGER
        elif distance <= self.config.warning_radius:
            return Zone.WARNING
        elif distance <= self.config.attention_radius:
            return Zone.ATTENTION
        elif distance <= self.config.awareness_radius:
            return Zone.AWARENESS
        else:
            return Zone.OUTSIDE
    
    def classify_by_zone(self, objects: List[Dict]) -> Dict[Zone, List[Dict]]:
        """
        تصنيف الأشياء حسب المنطقة
        
        Args:
            objects: قائمة الأشياء المكتشفة [{class, distance_m, ...}]
        
        Returns:
            dict: {Zone: [objects in that zone]}
        """
        classified = {zone: [] for zone in Zone}
        
        for obj in objects:
            distance = obj.get('distance_m', 999)
            zone = self.get_zone(distance)
            classified[zone].append({
                **obj,
                'zone': zone.value,
                'zone_priority': ZONE_PRIORITY[zone]
            })
        
        return classified
    
    def filter_alerts(self, objects: List[Dict]) -> List[Dict]:
        """
        فلترة التنبيهات - فقط الأشياء في المجال الشخصي
        
        لا ينبه للأشياء خارج المجال إلا:
        1. إذا المستخدم طلب مسح كامل (expanded_awareness)
        2. إذا الإعداد alert_outside_zone = True
        """
        # تحقق من انتهاء وقت التوسيع
        self._check_expansion_timeout()
        
        classified = self.classify_by_zone(objects)
        filtered = []
        
        # دائماً ينبه للمناطق الحرجة
        for zone in [Zone.DANGER, Zone.WARNING, Zone.ATTENTION, Zone.AWARENESS]:
            filtered.extend(classified[zone])
        
        # خارج المجال - فقط بشروط
        if self.config.expanded_awareness or self.config.alert_outside_zone:
            filtered.extend(classified[Zone.OUTSIDE])
        
        # ترتيب حسب الأولوية ثم المسافة
        filtered.sort(key=lambda x: (x.get('zone_priority', 5), x.get('distance_m', 999)))
        
        return filtered
    
    def get_zone_summary(self, objects: List[Dict]) -> Dict:
        """
        ملخص سريع للمناطق
        
        Returns:
            dict: {
                'danger_count': int,
                'warning_count': int,
                'closest_danger': dict or None,
                'message': str
            }
        """
        classified = self.classify_by_zone(objects)
        
        danger_objects = classified[Zone.DANGER]
        warning_objects = classified[Zone.WARNING]
        
        closest_danger = None
        if danger_objects:
            closest_danger = min(danger_objects, key=lambda x: x.get('distance_m', 999))
        
        # بناء الرسالة
        message = ""
        if danger_objects:
            names = [obj.get('class_ar', obj.get('class', 'شيء')) for obj in danger_objects[:2]]
            message = f"تحذير! {' و '.join(names)} قريب جداً منك"
        elif warning_objects:
            names = [obj.get('class_ar', obj.get('class', 'شيء')) for obj in warning_objects[:2]]
            message = f"انتبه! {' و '.join(names)} على بعد أقل من مترين"
        else:
            total = sum(len(classified[z]) for z in [Zone.ATTENTION, Zone.AWARENESS])
            if total > 0:
                message = f"يوجد {total} أشياء في محيطك"
            else:
                message = "المحيط خالي"
        
        return {
            'danger_count': len(danger_objects),
            'warning_count': len(warning_objects),
            'attention_count': len(classified[Zone.ATTENTION]),
            'awareness_count': len(classified[Zone.AWARENESS]),
            'outside_count': len(classified[Zone.OUTSIDE]),
            'closest_danger': closest_danger,
            'message': message,
            'expanded_awareness': self.config.expanded_awareness
        }
    
    def expand_awareness(self):
        """
        توسيع نطاق الوعي (بطلب المستخدم)
        مثلاً: المستخدم يقول "ماذا حولي؟"
        """
        self.config.expanded_awareness = True
        self.config.expansion_time = datetime.now()
        self.save_config()
        
        return {
            'message': 'تم توسيع نطاق الوعي، سأخبرك بكل شيء حولك',
            'duration': self.config.expansion_duration
        }
    
    def collapse_awareness(self):
        """تضييق نطاق الوعي (العودة للوضع العادي)"""
        self.config.expanded_awareness = False
        self.config.expansion_time = None
        self.save_config()
        
        return {'message': 'تم العودة للوضع العادي'}
    
    def _check_expansion_timeout(self):
        """التحقق من انتهاء وقت التوسيع"""
        if self.config.expanded_awareness and self.config.expansion_time:
            elapsed = (datetime.now() - self.config.expansion_time).total_seconds()
            if elapsed > self.config.expansion_duration:
                self.collapse_awareness()
    
    def update_zone_radius(self, zone: str, new_radius: float):
        """تعديل حد منطقة معينة"""
        if zone == 'danger':
            self.config.danger_radius = new_radius
        elif zone == 'warning':
            self.config.warning_radius = new_radius
        elif zone == 'attention':
            self.config.attention_radius = new_radius
        elif zone == 'awareness':
            self.config.awareness_radius = new_radius
        
        self.save_config()


# Instance عام للاستخدام المشترك
zone_system = ZoneSystem()
