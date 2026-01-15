"""
كاشف الثبات - Stationary Detector
يكتشف إذا كان المستخدم ثابتاً (جالساً) أو متحركاً

الغرض: تفعيل التعرف على الوجوه فقط عندما يكون المستخدم ثابتاً
لتجنب الإزعاج أثناء المشي
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import deque
from datetime import datetime
import numpy as np
import cv2


@dataclass
class MotionState:
    """حالة الحركة الحالية"""
    is_stationary: bool = False
    movement_level: float = 0.0  # 0 = ثابت تماماً، 1 = حركة كبيرة
    confidence: float = 0.0
    stationary_duration: float = 0.0  # مدة الثبات بالثواني
    last_significant_movement: Optional[datetime] = None


class StationaryDetector:
    """
    يكتشف حالة ثبات المستخدم باستخدام تحليل الفريمات
    """
    
    def __init__(self):
        # تاريخ الفريمات الأخيرة للمقارنة
        self.frame_history: deque = deque(maxlen=10)
        self.motion_history: deque = deque(maxlen=30)  # آخر 30 قياس
        
        # إعدادات الكشف
        self.movement_threshold = 0.02  # حد الحركة (2% تغيير = متحرك)
        self.stationary_time_threshold = 2.0  # ثانيتين للاعتبار ثابت
        
        # الحالة الحالية
        self.current_state = MotionState()
        self.last_frame_time: Optional[datetime] = None
        self.stationary_start_time: Optional[datetime] = None
        
        # Feature detection للمقارنة الذكية
        self.orb = None
        try:
            self.orb = cv2.ORB_create(nfeatures=500)
        except:
            pass
    
    def analyze_frame(self, image_bytes: bytes) -> MotionState:
        """
        يحلل الفريم الحالي ويحدد حالة الحركة
        
        Args:
            image_bytes: bytes الصورة
        
        Returns:
            MotionState: حالة الحركة
        """
        try:
            # تحويل لـ numpy array
            nparr = np.frombuffer(image_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is None:
                return self.current_state
            
            # تصغير الصورة للسرعة
            frame_small = cv2.resize(frame, (160, 120))
            gray = cv2.cvtColor(frame_small, cv2.COLOR_BGR2GRAY)
            
            current_time = datetime.now()
            
            if len(self.frame_history) > 0:
                # مقارنة مع الفريم السابق
                prev_gray = self.frame_history[-1]
                movement = self._calculate_movement(prev_gray, gray)
                
                self.motion_history.append(movement)
                
                # حساب متوسط الحركة
                avg_movement = np.mean(list(self.motion_history))
                
                # تحديث الحالة
                if avg_movement < self.movement_threshold:
                    if self.stationary_start_time is None:
                        self.stationary_start_time = current_time
                    
                    stationary_duration = (current_time - self.stationary_start_time).total_seconds()
                    
                    self.current_state = MotionState(
                        is_stationary=stationary_duration >= self.stationary_time_threshold,
                        movement_level=avg_movement,
                        confidence=min(1.0, stationary_duration / self.stationary_time_threshold),
                        stationary_duration=stationary_duration,
                        last_significant_movement=self.current_state.last_significant_movement
                    )
                else:
                    self.stationary_start_time = None
                    self.current_state = MotionState(
                        is_stationary=False,
                        movement_level=avg_movement,
                        confidence=1.0 - avg_movement,
                        stationary_duration=0.0,
                        last_significant_movement=current_time
                    )
            
            # حفظ الفريم الحالي
            self.frame_history.append(gray)
            self.last_frame_time = current_time
            
            return self.current_state
            
        except Exception as e:
            print(f"⚠️ Motion analysis error: {e}")
            return self.current_state
    
    def _calculate_movement(self, prev_frame: np.ndarray, curr_frame: np.ndarray) -> float:
        """
        حساب كمية الحركة بين فريمين
        يستخدم طريقة بسيطة وسريعة: Frame Difference
        """
        try:
            # طريقة 1: Frame Difference (سريعة)
            diff = cv2.absdiff(prev_frame, curr_frame)
            movement = np.mean(diff) / 255.0
            
            return movement
            
        except Exception:
            return 0.0
    
    def _calculate_movement_with_features(self, prev_frame: np.ndarray, curr_frame: np.ndarray) -> float:
        """
        حساب الحركة باستخدام Feature Matching (أدق لكن أبطأ)
        """
        if self.orb is None:
            return self._calculate_movement(prev_frame, curr_frame)
        
        try:
            # استخراج Features
            kp1, des1 = self.orb.detectAndCompute(prev_frame, None)
            kp2, des2 = self.orb.detectAndCompute(curr_frame, None)
            
            if des1 is None or des2 is None or len(des1) < 10 or len(des2) < 10:
                return self._calculate_movement(prev_frame, curr_frame)
            
            # مطابقة Features
            bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
            matches = bf.match(des1, des2)
            
            if len(matches) < 10:
                return 1.0  # حركة كبيرة (تغير المشهد)
            
            # حساب متوسط المسافة بين النقاط المتطابقة
            distances = []
            for m in matches[:50]:
                pt1 = np.array(kp1[m.queryIdx].pt)
                pt2 = np.array(kp2[m.trainIdx].pt)
                distances.append(np.linalg.norm(pt1 - pt2))
            
            # تطبيع المسافة
            max_dist = np.sqrt(prev_frame.shape[0]**2 + prev_frame.shape[1]**2)
            avg_dist = np.mean(distances) / max_dist
            
            return min(1.0, avg_dist * 10)  # scale up for sensitivity
            
        except Exception as e:
            return self._calculate_movement(prev_frame, curr_frame)
    
    def should_analyze_faces(self) -> bool:
        """
        هل يجب تحليل الوجوه الآن؟
        
        Returns:
            True إذا المستخدم ثابت لأكثر من الحد المطلوب
        """
        return self.current_state.is_stationary
    
    def get_status(self) -> Dict:
        """
        الحصول على حالة الكشف الحالية
        """
        return {
            'is_stationary': self.current_state.is_stationary,
            'movement_level': round(self.current_state.movement_level, 4),
            'confidence': round(self.current_state.confidence, 2),
            'stationary_duration': round(self.current_state.stationary_duration, 1),
            'should_analyze_faces': self.should_analyze_faces(),
            'message': self._get_status_message()
        }
    
    def _get_status_message(self) -> str:
        """رسالة حالة للتنقيح"""
        if self.current_state.is_stationary:
            return f"ثابت منذ {self.current_state.stationary_duration:.1f} ثانية"
        else:
            return f"متحرك (مستوى الحركة: {self.current_state.movement_level:.2%})"
    
    def reset(self):
        """إعادة تعيين الكاشف"""
        self.frame_history.clear()
        self.motion_history.clear()
        self.current_state = MotionState()
        self.stationary_start_time = None


# Instance عام
stationary_detector = StationaryDetector()
