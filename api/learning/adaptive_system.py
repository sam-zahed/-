"""
نظام التعلم التكيفي - Adaptive Learning System
يتعلم من سلوك المستخدم ويخصص التجربة

الآلية:
1. يراقب تفاعلات المستخدم مع التنبيهات
2. يتعلم التفضيلات (مثل: تجاهل تنبيهات الكراسي)
3. يعدل أولويات التنبيه حسب المستخدم
4. يتذكر الأماكن والأنماط المتكررة
"""

from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import json
from pathlib import Path


@dataclass
class UserPreference:
    """تفضيل مستخدم لنوع معين من التنبيهات"""
    object_class: str
    priority_adjustment: float  # -1 إلى 1 (سالب = أقل أهمية)
    ignore_count: int = 0       # عدد مرات التجاهل
    action_count: int = 0       # عدد مرات التفاعل
    last_updated: Optional[datetime] = None


@dataclass
class UsagePattern:
    """نمط استخدام متكرر"""
    pattern_type: str  # 'location', 'time', 'route'
    pattern_data: Dict = field(default_factory=dict)
    frequency: int = 0
    confidence: float = 0.0


@dataclass
class UserProfile:
    """ملف تعريف المستخدم"""
    user_id: str
    preferences: Dict[str, UserPreference] = field(default_factory=dict)
    patterns: List[UsagePattern] = field(default_factory=list)
    created_at: Optional[datetime] = None
    last_active: Optional[datetime] = None
    
    # إعدادات شخصية
    preferred_alert_intensity: str = "medium"  # low, medium, high
    alert_language: str = "ar"
    voice_speed: float = 1.0


class AdaptiveLearning:
    """
    نظام التعلم التكيفي من سلوك المستخدم
    """
    
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self.data_dir = Path(__file__).parent.parent / 'data' / 'learning'
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.profile = self._load_profile()
        
        # سجل التفاعلات للجلسة
        self.session_interactions: List[Dict] = []
        
        # إعدادات التعلم
        self.learning_rate = 0.1  # معدل التعلم
        self.min_samples_to_learn = 3  # أقل عدد عينات للبدء بالتعلم
        
    def _load_profile(self) -> UserProfile:
        """تحميل ملف تعريف المستخدم"""
        profile_path = self.data_dir / f'{self.user_id}_profile.json'
        
        if profile_path.exists():
            try:
                with open(profile_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    preferences = {}
                    for obj_class, pref_data in data.get('preferences', {}).items():
                        preferences[obj_class] = UserPreference(
                            object_class=obj_class,
                            priority_adjustment=pref_data.get('priority_adjustment', 0),
                            ignore_count=pref_data.get('ignore_count', 0),
                            action_count=pref_data.get('action_count', 0)
                        )
                    
                    return UserProfile(
                        user_id=self.user_id,
                        preferences=preferences,
                        preferred_alert_intensity=data.get('alert_intensity', 'medium'),
                        alert_language=data.get('language', 'ar'),
                        voice_speed=data.get('voice_speed', 1.0),
                        created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now()
                    )
            except Exception as e:
                print(f"⚠️ Error loading profile: {e}")
        
        return UserProfile(
            user_id=self.user_id,
            created_at=datetime.now()
        )
    
    def _save_profile(self):
        """حفظ ملف تعريف المستخدم"""
        try:
            profile_path = self.data_dir / f'{self.user_id}_profile.json'
            
            data = {
                'user_id': self.user_id,
                'created_at': self.profile.created_at.isoformat() if self.profile.created_at else None,
                'last_active': datetime.now().isoformat(),
                'preferences': {
                    obj: {
                        'priority_adjustment': pref.priority_adjustment,
                        'ignore_count': pref.ignore_count,
                        'action_count': pref.action_count
                    }
                    for obj, pref in self.profile.preferences.items()
                },
                'alert_intensity': self.profile.preferred_alert_intensity,
                'language': self.profile.alert_language,
                'voice_speed': self.profile.voice_speed
            }
            
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"⚠️ Error saving profile: {e}")
    
    def record_interaction(self, event_type: str, object_class: str, 
                          user_response: str, metadata: Dict = None):
        """
        تسجيل تفاعل المستخدم
        
        Args:
            event_type: نوع الحدث (alert_shown, alert_ignored, object_query, etc.)
            object_class: نوع الكائن
            user_response: استجابة المستخدم (acknowledged, ignored, asked_more, etc.)
            metadata: بيانات إضافية
        """
        interaction = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'object_class': object_class,
            'user_response': user_response,
            'metadata': metadata or {}
        }
        
        self.session_interactions.append(interaction)
        
        # تحليل وتعلم
        self._learn_from_interaction(event_type, object_class, user_response)
    
    def _learn_from_interaction(self, event_type: str, object_class: str, user_response: str):
        """
        التعلم من التفاعل
        """
        # إنشاء preference إذا لم يوجد
        if object_class not in self.profile.preferences:
            self.profile.preferences[object_class] = UserPreference(
                object_class=object_class,
                priority_adjustment=0.0
            )
        
        pref = self.profile.preferences[object_class]
        pref.last_updated = datetime.now()
        
        # تحديث حسب نوع الاستجابة
        if user_response == 'ignored':
            pref.ignore_count += 1
            # إذا تجاهل كثيراً، قلل الأولوية
            if pref.ignore_count >= self.min_samples_to_learn:
                pref.priority_adjustment = max(-0.5, pref.priority_adjustment - self.learning_rate)
                
        elif user_response == 'acknowledged':
            pref.action_count += 1
            # إذا تفاعل، ارفع الأولوية قليلاً
            pref.priority_adjustment = min(0.5, pref.priority_adjustment + self.learning_rate * 0.5)
            
        elif user_response == 'asked_more':
            pref.action_count += 1
            # طلب معلومات إضافية = اهتمام عالي
            pref.priority_adjustment = min(0.5, pref.priority_adjustment + self.learning_rate)
        
        # حفظ التغييرات
        self._save_profile()
    
    def get_personalized_priority(self, obj: Dict) -> int:
        """
        الحصول على أولوية مخصصة للمستخدم
        
        Args:
            obj: الكائن {class, priority, ...}
        
        Returns:
            int: الأولوية المعدلة (1 = أعلى)
        """
        base_priority = obj.get('priority', 3)
        object_class = obj.get('class', 'unknown')
        
        if object_class in self.profile.preferences:
            adjustment = self.profile.preferences[object_class].priority_adjustment
            
            # تعديل الأولوية (أقل = أهم)
            adjusted = base_priority - (adjustment * 2)
            return max(1, min(5, int(adjusted)))
        
        return base_priority
    
    def filter_by_preferences(self, objects: List[Dict]) -> List[Dict]:
        """
        فلترة وترتيب الكائنات حسب تفضيلات المستخدم
        """
        result = []
        
        for obj in objects:
            personalized_priority = self.get_personalized_priority(obj)
            
            # تخطي الكائنات المتجاهلة بشدة
            obj_class = obj.get('class', 'unknown')
            if obj_class in self.profile.preferences:
                pref = self.profile.preferences[obj_class]
                if pref.priority_adjustment < -0.4 and personalized_priority > 3:
                    continue  # تخطي
            
            result.append({
                **obj,
                'personalized_priority': personalized_priority
            })
        
        # ترتيب حسب الأولوية المخصصة
        result.sort(key=lambda x: x.get('personalized_priority', 5))
        
        return result
    
    def get_user_summary(self) -> Dict:
        """
        ملخص ملف تعريف المستخدم
        """
        ignored_objects = []
        favorite_objects = []
        
        for obj_class, pref in self.profile.preferences.items():
            if pref.priority_adjustment < -0.2:
                ignored_objects.append(obj_class)
            elif pref.priority_adjustment > 0.2:
                favorite_objects.append(obj_class)
        
        return {
            'user_id': self.user_id,
            'ignored_objects': ignored_objects,
            'favorite_objects': favorite_objects,
            'total_preferences': len(self.profile.preferences),
            'alert_intensity': self.profile.preferred_alert_intensity,
            'language': self.profile.alert_language,
            'voice_speed': self.profile.voice_speed,
            'session_interactions': len(self.session_interactions)
        }
    
    def update_settings(self, intensity: str = None, language: str = None, 
                       voice_speed: float = None) -> Dict:
        """
        تحديث إعدادات المستخدم
        """
        if intensity and intensity in ['low', 'medium', 'high']:
            self.profile.preferred_alert_intensity = intensity
        
        if language and language in ['ar', 'en', 'da']:
            self.profile.alert_language = language
        
        if voice_speed is not None:
            self.profile.voice_speed = max(0.5, min(2.0, voice_speed))
        
        self._save_profile()
        
        return {
            'message': 'تم تحديث الإعدادات',
            'alert_intensity': self.profile.preferred_alert_intensity,
            'language': self.profile.alert_language,
            'voice_speed': self.profile.voice_speed
        }
    
    def reset_preferences(self, object_class: str = None) -> Dict:
        """
        إعادة تعيين التفضيلات
        """
        if object_class:
            if object_class in self.profile.preferences:
                del self.profile.preferences[object_class]
                self._save_profile()
                return {'message': f'تم إعادة تعيين تفضيلات {object_class}'}
            return {'message': 'الكائن غير موجود في التفضيلات'}
        else:
            self.profile.preferences.clear()
            self._save_profile()
            return {'message': 'تم إعادة تعيين جميع التفضيلات'}
    
    def export_session_data(self) -> Dict:
        """
        تصدير بيانات الجلسة للتحليل
        """
        return {
            'user_id': self.user_id,
            'session_start': self.session_interactions[0]['timestamp'] if self.session_interactions else None,
            'interactions_count': len(self.session_interactions),
            'interactions': self.session_interactions
        }


# Instance عام
adaptive_learning = AdaptiveLearning()
