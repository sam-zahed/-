"""
مدير السياق - Context Manager
يتذكر سياق المحادثة والحالة الحالية

يحفظ:
- آخر الأشياء المرئية
- آخر رد
- حالة المستخدم (جالس/ماشي)
- تاريخ التفاعلات
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque


@dataclass
class ConversationTurn:
    """دور واحد في المحادثة"""
    timestamp: datetime
    user_input: Optional[str] = None
    assistant_response: Optional[str] = None
    detected_objects: List[Dict] = field(default_factory=list)
    action_taken: Optional[str] = None
    

@dataclass
class UserState:
    """حالة المستخدم الحالية"""
    is_stationary: bool = False
    is_walking: bool = False
    current_location: Optional[str] = None
    last_movement_time: Optional[datetime] = None
    facing_direction: Optional[str] = None


class ContextManager:
    """
    يدير سياق المحادثة والحالة
    يساعد المساعد على فهم ما يحدث
    """
    
    def __init__(self, max_history: int = 20):
        # تاريخ المحادثة
        self.conversation_history: deque = deque(maxlen=max_history)
        
        # آخر الأشياء المرئية
        self.last_objects: List[Dict] = []
        self.last_detection_time: Optional[datetime] = None
        
        # حالة المستخدم
        self.user_state = UserState()
        
        # الوضع الحالي
        self.quiet_mode: bool = False
        self.scanning_mode: bool = False
        
        # آخر رد
        self.last_response: Optional[str] = None
        self.last_response_time: Optional[datetime] = None
        
        # الأشياء المذكورة حديثاً (لتجنب التكرار)
        self.recently_mentioned: Dict[str, datetime] = {}
        
        # سؤال معلق ينتظر رد
        self.pending_question: Optional[str] = None
        
    def update_objects(self, objects: List[Dict]):
        """تحديث الأشياء المرئية"""
        self.last_objects = objects
        self.last_detection_time = datetime.now()
        
    def add_conversation_turn(self, 
                              user_input: Optional[str] = None,
                              assistant_response: Optional[str] = None,
                              action: Optional[str] = None):
        """إضافة دور في المحادثة"""
        turn = ConversationTurn(
            timestamp=datetime.now(),
            user_input=user_input,
            assistant_response=assistant_response,
            detected_objects=self.last_objects.copy(),
            action_taken=action
        )
        self.conversation_history.append(turn)
        
        if assistant_response:
            self.last_response = assistant_response
            self.last_response_time = datetime.now()
    
    def update_user_state(self, 
                         is_stationary: Optional[bool] = None,
                         is_walking: Optional[bool] = None,
                         location: Optional[str] = None):
        """تحديث حالة المستخدم"""
        if is_stationary is not None:
            self.user_state.is_stationary = is_stationary
            self.user_state.is_walking = not is_stationary
        if is_walking is not None:
            self.user_state.is_walking = is_walking
            self.user_state.is_stationary = not is_walking
        if location:
            self.user_state.current_location = location
            
        self.user_state.last_movement_time = datetime.now()
    
    def set_quiet_mode(self, quiet: bool):
        """تفعيل/إلغاء وضع الصمت"""
        self.quiet_mode = quiet
        return {
            'quiet_mode': quiet,
            'message': 'وضع الصمت نشط' if quiet else 'وضع الصمت ملغي'
        }
    
    def set_scanning_mode(self, scanning: bool):
        """تفعيل/إلغاء وضع المسح"""
        self.scanning_mode = scanning
        return {
            'scanning_mode': scanning,
            'message': 'وضع المسح نشط' if scanning else 'وضع المسح ملغي'
        }
    
    def mark_mentioned(self, obj_class: str):
        """تسجيل أننا ذكرنا هذا الشيء"""
        self.recently_mentioned[obj_class] = datetime.now()
    
    def was_recently_mentioned(self, obj_class: str, seconds: int = 30) -> bool:
        """هل ذكرنا هذا الشيء حديثاً؟"""
        if obj_class not in self.recently_mentioned:
            return False
        
        elapsed = (datetime.now() - self.recently_mentioned[obj_class]).total_seconds()
        return elapsed < seconds
    
    def get_last_objects_by_class(self, obj_class: str) -> List[Dict]:
        """الحصول على آخر الأشياء من نوع معين"""
        return [obj for obj in self.last_objects 
                if obj.get('class', '').lower() == obj_class.lower()]
    
    def get_closest_object(self) -> Optional[Dict]:
        """الحصول على أقرب شيء"""
        if not self.last_objects:
            return None
        return min(self.last_objects, key=lambda x: x.get('distance_m', 999))
    
    def get_objects_in_direction(self, direction: str) -> List[Dict]:
        """الحصول على الأشياء في اتجاه معين"""
        direction_map = {
            'امام': 'front', 'أمام': 'front', 'قدام': 'front',
            'يمين': 'right', 'يمينك': 'right',
            'يسار': 'left', 'شمال': 'left', 'يسارك': 'left',
            'خلف': 'back', 'ورا': 'back'
        }
        
        normalized = direction_map.get(direction, direction)
        
        return [obj for obj in self.last_objects 
                if obj.get('direction', '').lower() == normalized.lower()]
    
    def get_context_summary(self) -> Dict:
        """ملخص السياق الحالي"""
        return {
            'is_stationary': self.user_state.is_stationary,
            'quiet_mode': self.quiet_mode,
            'scanning_mode': self.scanning_mode,
            'objects_count': len(self.last_objects),
            'last_detection': self.last_detection_time.isoformat() if self.last_detection_time else None,
            'last_response': self.last_response,
            'conversation_turns': len(self.conversation_history)
        }
    
    def get_last_conversation(self, n: int = 5) -> List[Dict]:
        """آخر n أدوار في المحادثة"""
        history = list(self.conversation_history)[-n:]
        return [
            {
                'user': turn.user_input,
                'assistant': turn.assistant_response,
                'action': turn.action_taken,
                'time': turn.timestamp.isoformat()
            }
            for turn in history
        ]
    
    def clear_context(self):
        """مسح السياق"""
        self.conversation_history.clear()
        self.last_objects = []
        self.recently_mentioned.clear()
        self.pending_question = None


# Instance عام
context_manager = ContextManager()
