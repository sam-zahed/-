"""
دليل المشي المستقيم - Straight Walk Guide
يساعد الكفيف على المشي في خط مستقيم

الآلية:
1. يحدد خطين افتراضيين أمام المستخدم كـ "ممر"
2. يتتبع انحراف الكاميرا عن هذا الممر
3. ينبه بلطف عند الانحراف يميناً أو يساراً
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import deque
from datetime import datetime
import numpy as np
import cv2


@dataclass
class DeviationState:
    """حالة الانحراف الحالية"""
    deviation: str  # 'left', 'right', 'center'
    deviation_amount: float  # 0-1, نسبة الانحراف
    should_alert: bool
    alert_message: str
    confidence: float
    timestamp: datetime = None


@dataclass
class WalkingPath:
    """المسار الافتراضي للمشي"""
    left_line: Tuple[float, float]  # (x1, x2) normalized 0-1
    right_line: Tuple[float, float]
    center_point: float  # x normalized
    is_calibrated: bool = False


class StraightWalkGuide:
    """
    نظام توجيه المشي المستقيم للمكفوفين
    
    يستخدم تحليل الصورة لتحديد:
    1. Vanishing point - نقطة التلاشي (أفق المشي)
    2. خطوط الأرضية والجدران
    3. اتجاه الكاميرا (وبالتالي المستخدم)
    """
    
    def __init__(self):
        # إعدادات المسار
        self.default_path = WalkingPath(
            left_line=(0.3, 0.35),   # 30-35% من اليسار
            right_line=(0.65, 0.7), # 65-70% من اليمين
            center_point=0.5,        # المركز
            is_calibrated=False
        )
        self.current_path = self.default_path
        
        # تاريخ الانحرافات للتنعيم
        self.deviation_history: deque = deque(maxlen=10)
        
        # إعدادات التنبيه
        self.deviation_threshold = 0.15  # 15% انحراف قبل التنبيه
        self.alert_cooldown = 5.0  # ثواني بين التنبيهات
        self.last_alert_time: Optional[datetime] = None
        
        # حالة التتبع
        self.is_tracking = False
        self.reference_frame = None
        
    def start_tracking(self, initial_frame_bytes: bytes = None) -> Dict:
        """
        بدء تتبع المشي المستقيم
        
        Args:
            initial_frame_bytes: صورة البداية لتحديد المسار
        """
        self.is_tracking = True
        self.deviation_history.clear()
        
        if initial_frame_bytes:
            self.calibrate_path(initial_frame_bytes)
        
        return {
            'message': 'تم بدء تتبع المشي. امشِ للأمام وسأنبهك إذا انحرفت',
            'is_tracking': True,
            'path_calibrated': self.current_path.is_calibrated
        }
    
    def stop_tracking(self) -> Dict:
        """إيقاف التتبع"""
        self.is_tracking = False
        return {
            'message': 'تم إيقاف تتبع المشي',
            'is_tracking': False
        }
    
    def calibrate_path(self, frame_bytes: bytes) -> Dict:
        """
        معايرة المسار من الصورة الحالية
        يحاول تحديد خطوط الأرضية/الجدران
        """
        try:
            # تحويل لـ numpy
            nparr = np.frombuffer(frame_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is None:
                return {'success': False, 'message': 'لم أستطع قراءة الصورة'}
            
            # استخراج خطوط Hough
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            
            # البحث عن الخطوط
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, 50, 
                                    minLineLength=100, maxLineGap=50)
            
            if lines is not None and len(lines) > 0:
                # تحليل الخطوط لتحديد حواف المسار
                left_lines = []
                right_lines = []
                h, w = frame.shape[:2]
                center_x = w / 2
                
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    
                    # حساب الميل
                    if x2 - x1 != 0:
                        slope = (y2 - y1) / (x2 - x1)
                        
                        # خط مائل = حافة مسار محتملة
                        if abs(slope) > 0.3 and abs(slope) < 3:
                            mid_x = (x1 + x2) / 2
                            if mid_x < center_x:
                                left_lines.append(mid_x / w)
                            else:
                                right_lines.append(mid_x / w)
                
                if left_lines and right_lines:
                    self.current_path = WalkingPath(
                        left_line=(min(left_lines), np.mean(left_lines)),
                        right_line=(np.mean(right_lines), max(right_lines)),
                        center_point=(np.mean(left_lines) + np.mean(right_lines)) / 2,
                        is_calibrated=True
                    )
                    
                    return {
                        'success': True,
                        'message': 'تم تحديد مسار المشي',
                        'path_width': self.current_path.right_line[0] - self.current_path.left_line[1]
                    }
            
            # إذا لم ننجح، نستخدم المسار الافتراضي
            return {
                'success': False,
                'message': 'لم أستطع تحديد مسار واضح، سأستخدم الإعدادات الافتراضية'
            }
            
        except Exception as e:
            return {'success': False, 'message': f'خطأ في المعايرة: {str(e)}'}
    
    def analyze_deviation(self, frame_bytes: bytes) -> DeviationState:
        """
        تحليل انحراف المستخدم عن المسار المستقيم
        
        Returns:
            DeviationState: حالة الانحراف
        """
        try:
            # تحويل الصورة
            nparr = np.frombuffer(frame_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is None:
                return self._get_default_state()
            
            h, w = frame.shape[:2]
            
            # تحليل بسيط: مقارنة كثافة اليسار واليمين
            # في الممرات، الجانب الأقرب للجدار يكون أغمق عادة
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # منطقة الأرضية (النصف السفلي)
            floor_region = gray[int(h*0.6):, :]
            
            # تقسيم لجزء يسار ويمين
            mid = floor_region.shape[1] // 2
            left_intensity = np.mean(floor_region[:, :mid])
            right_intensity = np.mean(floor_region[:, mid:])
            
            # تحليل الاختلاف
            diff = (right_intensity - left_intensity) / 255.0
            
            # تحديد الانحراف
            if abs(diff) < self.deviation_threshold / 3:
                deviation = 'center'
                deviation_amount = abs(diff)
            elif diff > 0:
                deviation = 'left'  # يميل لليسار (الجانب الأيمن أفتح = أقرب للمركز)
                deviation_amount = min(1.0, abs(diff) * 2)
            else:
                deviation = 'right'
                deviation_amount = min(1.0, abs(diff) * 2)
            
            # حفظ في التاريخ
            self.deviation_history.append(deviation_amount * (1 if deviation == 'right' else -1 if deviation == 'left' else 0))
            
            # حساب متوسط
            avg_deviation = np.mean(list(self.deviation_history)) if self.deviation_history else 0
            
            # تحديد إذا يجب التنبيه
            should_alert, alert_message = self._should_alert(deviation, deviation_amount, avg_deviation)
            
            state = DeviationState(
                deviation=deviation,
                deviation_amount=deviation_amount,
                should_alert=should_alert,
                alert_message=alert_message,
                confidence=min(1.0, 0.5 + abs(avg_deviation)),
                timestamp=datetime.now()
            )
            
            return state
            
        except Exception as e:
            print(f"⚠️ Deviation analysis error: {e}")
            return self._get_default_state()
    
    def _should_alert(self, deviation: str, amount: float, avg: float) -> Tuple[bool, str]:
        """
        تحديد إذا يجب إصدار تنبيه
        """
        now = datetime.now()
        
        # فحص cooldown
        if self.last_alert_time:
            elapsed = (now - self.last_alert_time).total_seconds()
            if elapsed < self.alert_cooldown:
                return False, ""
        
        # لا تنبه إذا في المركز
        if deviation == 'center':
            return False, ""
        
        # تنبه فقط إذا الانحراف كبير ومستمر
        if abs(avg) > self.deviation_threshold:
            self.last_alert_time = now
            
            if deviation == 'left':
                if amount > 0.3:
                    return True, "انحرفت يساراً كثير، ارجع يمين"
                else:
                    return True, "مايل يسار قليل"
            else:
                if amount > 0.3:
                    return True, "انحرفت يميناً كثير، ارجع يسار"
                else:
                    return True, "مايل يمين قليل"
        
        return False, ""
    
    def _get_default_state(self) -> DeviationState:
        """حالة افتراضية"""
        return DeviationState(
            deviation='center',
            deviation_amount=0.0,
            should_alert=False,
            alert_message='',
            confidence=0.0,
            timestamp=datetime.now()
        )
    
    def get_status(self) -> Dict:
        """الحصول على حالة التتبع"""
        return {
            'is_tracking': self.is_tracking,
            'path_calibrated': self.current_path.is_calibrated,
            'deviation_threshold': self.deviation_threshold,
            'alert_cooldown': self.alert_cooldown
        }
    
    def update_settings(self, threshold: float = None, cooldown: float = None) -> Dict:
        """تحديث إعدادات التتبع"""
        if threshold is not None:
            self.deviation_threshold = max(0.05, min(0.5, threshold))
        if cooldown is not None:
            self.alert_cooldown = max(1.0, min(30.0, cooldown))
        
        return {
            'message': 'تم تحديث الإعدادات',
            'deviation_threshold': self.deviation_threshold,
            'alert_cooldown': self.alert_cooldown
        }
    
    def reset(self):
        """إعادة تعيين النظام"""
        self.is_tracking = False
        self.current_path = self.default_path
        self.deviation_history.clear()
        self.last_alert_time = None


# Instance عام
straight_walk_guide = StraightWalkGuide()
