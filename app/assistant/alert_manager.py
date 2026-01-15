"""
مدير التنبيهات الذكي - Smart Alert Manager
يتحكم في التنبيهات بذكاء لتجنب الإزعاج

المشكلة: النظام القديم ينبه على كل شيء = تشتيت
الحل: تنبيهات ذكية بناءً على السياق
"""

from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
from pathlib import Path


class AlertMode(Enum):
    """أوضاع التنبيه"""
    NORMAL = "normal"       # عادي - كل الأشياء المهمة
    QUIET = "quiet"         # صامت - فقط الأخطار
    WALKING = "walking"     # مشي - تركيز على العوائق
    SCANNING = "scanning"   # مسح - كل شيء مرة واحدة


# الأشياء التي تستحق تنبيه فوري دائماً
ALWAYS_ALERT = {
    'stairs', 'staircase', 'steps', 'hole', 'pothole', 
    'car', 'truck', 'bus', 'motorcycle', 'bicycle',
    'escalator', 'elevator'
}

# الأشياء التي ننبه عليها عند الاقتراب فقط
ALERT_WHEN_CLOSE = {
    'person', 'child', 'door', 'wall', 'obstacle',
    'chair', 'table', 'pillar'
}

# الأشياء التي نتجاهلها عادة
USUALLY_IGNORE = {
    'floor', 'ceiling', 'window', 'picture', 'plant',
    'lamp', 'curtain', 'rug', 'carpet'
}


@dataclass
class AlertCooldown:
    """معلومات التهدئة لنوع معين"""
    object_class: str
    last_alert_time: datetime
    alert_count: int = 0
    

@dataclass
class AlertDecision:
    """قرار التنبيه"""
    should_alert: bool
    reason: str
    priority: int = 3  # 1 = عاجل، 5 = عادي
    message: Optional[str] = None
    cooldown_remaining: float = 0.0


class SmartAlertManager:
    """
    مدير التنبيهات الذكي
    يقرر متى وكيف ننبه المستخدم
    """
    
    def __init__(self):
        # إعدادات التهدئة (cooldown) بالثواني
        self.cooldowns = {
            'stairs': 5,      # أخطار - تكرار سريع
            'hole': 5,
            'car': 3,
            'person': 30,     # أشخاص - مرة كل نصف دقيقة
            'door': 60,       # أبواب - مرة كل دقيقة
            'chair': 120,     # أثاث - مرة كل دقيقتين
            'default': 30     # افتراضي
        }
        
        # سجل آخر تنبيه لكل نوع
        self.last_alerts: Dict[str, AlertCooldown] = {}
        
        # الوضع الحالي
        self.current_mode = AlertMode.NORMAL
        
        # هل المستخدم ثابت؟
        self.is_stationary = False
        
        # آخر الأشياء المرئية (لكشف الجديد)
        self.recently_seen: Dict[str, datetime] = {}
        
        # عدد التنبيهات في الدقيقة الأخيرة (لمنع الإغراق)
        self.alerts_last_minute: List[datetime] = []
        self.max_alerts_per_minute = 5
        
    def set_mode(self, mode: AlertMode):
        """تغيير وضع التنبيه"""
        self.current_mode = mode
        return {'mode': mode.value, 'message': self._get_mode_message(mode)}
    
    def _get_mode_message(self, mode: AlertMode) -> str:
        """رسالة تأكيد تغيير الوضع"""
        messages = {
            AlertMode.NORMAL: "وضع التنبيهات العادي",
            AlertMode.QUIET: "وضع الصمت - فقط الأخطار",
            AlertMode.WALKING: "وضع المشي - تركيز على العوائق",
            AlertMode.SCANNING: "وضع المسح - سأخبرك بكل شيء"
        }
        return messages.get(mode, "")
    
    def set_stationary(self, is_stationary: bool):
        """تحديث حالة الثبات"""
        self.is_stationary = is_stationary
    
    def should_alert(self, obj: Dict) -> AlertDecision:
        """
        هل يجب التنبيه على هذا الشيء؟
        
        Args:
            obj: الشيء المكتشف {class, distance_m, ...}
        
        Returns:
            AlertDecision: قرار التنبيه
        """
        obj_class = obj.get('class', 'unknown').lower()
        distance = obj.get('distance_m', 999)
        
        # 1. فحص الإغراق - لا نريد أكثر من 5 تنبيهات في الدقيقة
        self._cleanup_old_alerts()
        if len(self.alerts_last_minute) >= self.max_alerts_per_minute:
            if obj_class not in ALWAYS_ALERT:
                return AlertDecision(
                    should_alert=False,
                    reason="too_many_alerts",
                    message="تم تجاوز حد التنبيهات"
                )
        
        # 2. في وضع الصمت - فقط الأخطار
        if self.current_mode == AlertMode.QUIET:
            if obj_class not in ALWAYS_ALERT:
                return AlertDecision(
                    should_alert=False,
                    reason="quiet_mode",
                    message="وضع الصمت نشط"
                )
        
        # 3. إذا ثابت (جالس) - فقط الأشياء المهمة جداً أو القريبة جداً
        if self.is_stationary and self.current_mode == AlertMode.NORMAL:
            if obj_class in USUALLY_IGNORE:
                return AlertDecision(
                    should_alert=False,
                    reason="stationary_ignore",
                    message="متجاهل أثناء الجلوس"
                )
            # إذا ليس خطراً وبعيد > 1.5 متر، تجاهل
            if obj_class not in ALWAYS_ALERT and distance > 1.5:
                return AlertDecision(
                    should_alert=False,
                    reason="stationary_far",
                    message="ثابت وبعيد"
                )
        
        # 4. فحص التهدئة (cooldown)
        cooldown_secs = self.cooldowns.get(obj_class, self.cooldowns['default'])
        
        if obj_class in self.last_alerts:
            last = self.last_alerts[obj_class]
            elapsed = (datetime.now() - last.last_alert_time).total_seconds()
            
            if elapsed < cooldown_secs:
                # لم يمر وقت كافٍ
                # إلا إذا اقترب كثيراً (خطر)
                if distance > 0.5 or obj_class not in ALWAYS_ALERT:
                    return AlertDecision(
                        should_alert=False,
                        reason="cooldown",
                        cooldown_remaining=cooldown_secs - elapsed,
                        message=f"تم التنبيه قبل {int(elapsed)} ثانية"
                    )
        
        # 5. فحص المسافة
        if distance > 6.0 and obj_class not in ALWAYS_ALERT:
            return AlertDecision(
                should_alert=False,
                reason="too_far",
                message="بعيد جداً"
            )
        
        # 6. فحص الأشياء المتجاهلة عادة
        if obj_class in USUALLY_IGNORE and self.current_mode != AlertMode.SCANNING:
            return AlertDecision(
                should_alert=False,
                reason="usually_ignored",
                message="نوع متجاهل عادة"
            )
        
        # === نعم، يجب التنبيه ===
        
        # تحديد الأولوية
        priority = self._calculate_priority(obj_class, distance)
        
        # تسجيل التنبيه
        self._record_alert(obj_class)
        
        # توليد الرسالة
        message = self._generate_message(obj, priority)
        
        return AlertDecision(
            should_alert=True,
            reason="approved",
            priority=priority,
            message=message
        )
    
    def _calculate_priority(self, obj_class: str, distance: float) -> int:
        """حساب أولوية التنبيه (1 = عاجل جداً)"""
        if obj_class in ALWAYS_ALERT:
            if distance < 1.0:
                return 1  # خطر فوري
            elif distance < 2.0:
                return 2
            else:
                return 3
        elif obj_class in ALERT_WHEN_CLOSE:
            if distance < 0.5:
                return 2
            elif distance < 1.5:
                return 3
            else:
                return 4
        else:
            return 5
    
    def _generate_message(self, obj: Dict, priority: int) -> str:
        """توليد رسالة التنبيه"""
        obj_class = obj.get('class_ar', obj.get('class', 'شيء'))
        distance = obj.get('distance_m', 0)
        direction = obj.get('direction_ar', 'أمامك')
        
        if priority == 1:
            return f"تحذير! {obj_class} قريب جداً!"
        elif priority == 2:
            return f"انتبه! {obj_class} على بعد متر"
        elif priority <= 3:
            if distance < 2:
                return f"{obj_class} {direction}"
            else:
                return f"{obj_class} على بعد {int(distance)} متر"
        else:
            return f"{obj_class}"
    
    def _record_alert(self, obj_class: str):
        """تسجيل التنبيه"""
        now = datetime.now()
        
        if obj_class in self.last_alerts:
            self.last_alerts[obj_class].last_alert_time = now
            self.last_alerts[obj_class].alert_count += 1
        else:
            self.last_alerts[obj_class] = AlertCooldown(
                object_class=obj_class,
                last_alert_time=now,
                alert_count=1
            )
        
        self.alerts_last_minute.append(now)
    
    def _cleanup_old_alerts(self):
        """تنظيف التنبيهات القديمة"""
        one_minute_ago = datetime.now() - timedelta(minutes=1)
        self.alerts_last_minute = [
            t for t in self.alerts_last_minute 
            if t > one_minute_ago
        ]
    
    def filter_objects(self, objects: List[Dict]) -> List[Dict]:
        """
        فلترة قائمة الأشياء وإرجاع فقط ما يستحق التنبيه
        """
        filtered = []
        
        for obj in objects:
            decision = self.should_alert(obj)
            if decision.should_alert:
                filtered.append({
                    **obj,
                    'alert_priority': decision.priority,
                    'alert_message': decision.message
                })
        
        # ترتيب حسب الأولوية
        filtered.sort(key=lambda x: x.get('alert_priority', 5))
        
        return filtered
    
    def get_speak_message(self, objects: List[Dict], max_items: int = 3) -> str:
        """
        توليد رسالة صوتية واحدة من قائمة الأشياء
        بدلاً من تنبيه على كل شيء، رسالة واحدة مختصرة
        """
        filtered = self.filter_objects(objects)
        
        if not filtered:
            return ""
        
        # أهم 3 أشياء فقط
        top_items = filtered[:max_items]
        
        messages = [item.get('alert_message', '') for item in top_items]
        messages = [m for m in messages if m]
        
        if len(messages) == 1:
            return messages[0]
        elif len(messages) == 2:
            return f"{messages[0]}، و{messages[1]}"
        else:
            return ". ".join(messages)
    
    def reset_cooldowns(self):
        """إعادة تعيين كل التهدئة"""
        self.last_alerts.clear()
        self.alerts_last_minute.clear()
    
    def get_status(self) -> Dict:
        """حالة مدير التنبيهات"""
        return {
            'mode': self.current_mode.value,
            'is_stationary': self.is_stationary,
            'alerts_last_minute': len(self.alerts_last_minute),
            'max_alerts_per_minute': self.max_alerts_per_minute,
            'active_cooldowns': len(self.last_alerts)
        }


# Instance عام
alert_manager = SmartAlertManager()
