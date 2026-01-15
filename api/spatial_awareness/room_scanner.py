"""
ماسح الغرفة - Room Scanner
يدير عملية مسح الغرفة 360 درجة للتعرف على المحيط

يطلب من المستخدم الدوران ببطء لتسجيل كل الاتجاهات
ثم يبني خريطة أساسية للغرفة
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
from pathlib import Path
import numpy as np


class ScanDirection(Enum):
    """اتجاهات المسح"""
    FRONT = "front"
    FRONT_RIGHT = "front_right"
    RIGHT = "right"
    BACK_RIGHT = "back_right"
    BACK = "back"
    BACK_LEFT = "back_left"
    LEFT = "left"
    FRONT_LEFT = "front_left"


# ترتيب الاتجاهات للمسح (عكس عقارب الساعة)
SCAN_ORDER = [
    ScanDirection.FRONT,
    ScanDirection.FRONT_LEFT,
    ScanDirection.LEFT,
    ScanDirection.BACK_LEFT,
    ScanDirection.BACK,
    ScanDirection.BACK_RIGHT,
    ScanDirection.RIGHT,
    ScanDirection.FRONT_RIGHT
]

# رسائل الإرشاد بالعربية
DIRECTION_PROMPTS_AR = {
    ScanDirection.FRONT: "ابق على هذا الاتجاه",
    ScanDirection.FRONT_LEFT: "لف قليلاً لليسار",
    ScanDirection.LEFT: "استمر في اللف لليسار",
    ScanDirection.BACK_LEFT: "واصل اللف لليسار",
    ScanDirection.BACK: "الآن خلفك",
    ScanDirection.BACK_RIGHT: "لف لليمين الآن",
    ScanDirection.RIGHT: "استمر لليمين",
    ScanDirection.FRONT_RIGHT: "أوشكت على الانتهاء، لف قليلاً لليمين"
}


@dataclass
class DirectionScan:
    """بيانات مسح اتجاه واحد"""
    direction: ScanDirection
    objects: List[Dict] = field(default_factory=list)
    scanned_at: Optional[datetime] = None
    is_complete: bool = False


@dataclass
class RoomScanSession:
    """جلسة مسح غرفة كاملة"""
    session_id: str
    user_id: str
    room_name: str = "غرفة"
    scans: Dict[str, DirectionScan] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    is_complete: bool = False
    current_direction_index: int = 0


class RoomScanner:
    """
    يدير عملية مسح الغرفة 360 درجة
    """
    
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent / 'data' / 'rooms'
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.active_sessions: Dict[str, RoomScanSession] = {}
    
    def start_scan(self, user_id: str, room_name: str = "غرفة") -> Dict:
        """
        يبدأ جلسة مسح جديدة
        
        Returns:
            dict: {session_id, instructions, first_prompt}
        """
        import uuid
        session_id = str(uuid.uuid4())[:8]
        
        session = RoomScanSession(
            session_id=session_id,
            user_id=user_id,
            room_name=room_name,
            started_at=datetime.now(),
            scans={d.value: DirectionScan(direction=d) for d in SCAN_ORDER}
        )
        
        self.active_sessions[session_id] = session
        
        first_direction = SCAN_ORDER[0]
        
        return {
            'session_id': session_id,
            'message': f"لنبدأ مسح {room_name}. ابدأ من الأمام واتبع الإرشادات",
            'instructions': "لف ببطء 360 درجة لمسح محيطك. سأخبرك بما أكتشفه في كل اتجاه",
            'current_direction': first_direction.value,
            'prompt': DIRECTION_PROMPTS_AR[first_direction],
            'progress': 0,
            'total_directions': len(SCAN_ORDER)
        }
    
    def process_scan_frame(self, session_id: str, objects: List[Dict], 
                           estimated_angle: float = None) -> Dict:
        """
        يعالج frame أثناء المسح
        
        Args:
            session_id: معرف الجلسة
            objects: الأشياء المكتشفة في الـ frame
            estimated_angle: الزاوية التقديرية (0-360)
        
        Returns:
            dict: {direction, objects_found, next_prompt, progress}
        """
        if session_id not in self.active_sessions:
            return {'error': 'جلسة غير موجودة'}
        
        session = self.active_sessions[session_id]
        
        if session.is_complete:
            return {'error': 'المسح مكتمل بالفعل', 'session_id': session_id}
        
        # تحديد الاتجاه الحالي
        current_direction = SCAN_ORDER[session.current_direction_index]
        
        # تحديث بيانات المسح
        scan = session.scans[current_direction.value]
        scan.objects.extend(objects)
        scan.scanned_at = datetime.now()
        scan.is_complete = True
        
        # الانتقال للاتجاه التالي
        session.current_direction_index += 1
        progress = session.current_direction_index / len(SCAN_ORDER)
        
        if session.current_direction_index >= len(SCAN_ORDER):
            # المسح اكتمل
            session.is_complete = True
            session.completed_at = datetime.now()
            
            # حفظ النتائج
            self._save_scan_results(session)
            
            return {
                'session_id': session_id,
                'direction': current_direction.value,
                'objects_found': len(objects),
                'is_complete': True,
                'progress': 100,
                'message': 'تم اكتمال المسح! لقد تعرفت على محيطك',
                'summary': self._generate_room_summary(session)
            }
        
        # الاتجاه التالي
        next_direction = SCAN_ORDER[session.current_direction_index]
        
        return {
            'session_id': session_id,
            'direction': current_direction.value,
            'objects_found': len(objects),
            'is_complete': False,
            'progress': int(progress * 100),
            'next_direction': next_direction.value,
            'next_prompt': DIRECTION_PROMPTS_AR[next_direction],
            'message': f"جيد! وجدت {len(objects)} أشياء. {DIRECTION_PROMPTS_AR[next_direction]}"
        }
    
    def _generate_room_summary(self, session: RoomScanSession) -> Dict:
        """توليد ملخص الغرفة بعد المسح"""
        all_objects = {}
        total_objects = 0
        
        for direction, scan in session.scans.items():
            for obj in scan.objects:
                obj_class = obj.get('class_ar', obj.get('class', 'شيء'))
                if obj_class not in all_objects:
                    all_objects[obj_class] = {'count': 0, 'directions': []}
                all_objects[obj_class]['count'] += 1
                if direction not in all_objects[obj_class]['directions']:
                    all_objects[obj_class]['directions'].append(direction)
                total_objects += 1
        
        # ترتيب حسب الأكثر تكراراً
        sorted_objects = sorted(all_objects.items(), key=lambda x: x[1]['count'], reverse=True)
        
        # بناء الملخص النصي
        summary_parts = []
        for obj_name, obj_data in sorted_objects[:5]:
            directions = obj_data['directions']
            if len(directions) == 1:
                summary_parts.append(f"{obj_name} في {directions[0]}")
            else:
                summary_parts.append(f"{obj_name} في عدة اتجاهات")
        
        return {
            'total_objects': total_objects,
            'unique_objects': len(all_objects),
            'objects': dict(sorted_objects[:10]),
            'summary_text': 'يوجد في المحيط: ' + '، '.join(summary_parts) if summary_parts else 'لم أجد أشياء'
        }
    
    def _save_scan_results(self, session: RoomScanSession):
        """حفظ نتائج المسح"""
        try:
            result = {
                'session_id': session.session_id,
                'user_id': session.user_id,
                'room_name': session.room_name,
                'scanned_at': session.completed_at.isoformat() if session.completed_at else None,
                'scans': {}
            }
            
            for direction, scan in session.scans.items():
                result['scans'][direction] = {
                    'objects': scan.objects,
                    'scanned_at': scan.scanned_at.isoformat() if scan.scanned_at else None
                }
            
            # حفظ كملف
            file_path = self.data_dir / f'{session.user_id}_{session.session_id}.json'
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"⚠️ Error saving scan: {e}")
    
    def get_session_status(self, session_id: str) -> Dict:
        """الحصول على حالة جلسة المسح"""
        if session_id not in self.active_sessions:
            return {'error': 'جلسة غير موجودة'}
        
        session = self.active_sessions[session_id]
        
        return {
            'session_id': session_id,
            'is_complete': session.is_complete,
            'progress': int((session.current_direction_index / len(SCAN_ORDER)) * 100),
            'current_direction': SCAN_ORDER[min(session.current_direction_index, len(SCAN_ORDER)-1)].value
        }
    
    def cancel_scan(self, session_id: str) -> Dict:
        """إلغاء جلسة المسح"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            return {'message': 'تم إلغاء المسح', 'success': True}
        return {'error': 'جلسة غير موجودة', 'success': False}
    
    def get_saved_rooms(self, user_id: str) -> List[Dict]:
        """الحصول على قائمة الغرف المحفوظة للمستخدم"""
        rooms = []
        for file_path in self.data_dir.glob(f'{user_id}_*.json'):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    rooms.append({
                        'session_id': data.get('session_id'),
                        'room_name': data.get('room_name'),
                        'scanned_at': data.get('scanned_at')
                    })
            except:
                continue
        return rooms


# Instance عام
room_scanner = RoomScanner()
