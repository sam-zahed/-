"""
البيئة الأساسية - Environment Baseline
يميز بين الأشياء الثابتة (الأثاث، الجدران) والمتغيرة (الأشخاص، الحيوانات)

الهدف: تحديد ما هو "طبيعي" في المحيط وما هو "مفاجأة"
"""

from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path


# الأشياء الثابتة دائماً (لا تتحرك عادة)
ALWAYS_FIXED = {
    'wall', 'door', 'window', 'stairs', 'staircase', 'floor', 'ceiling',
    'elevator', 'escalator', 'pillar', 'column',
    'sink', 'toilet', 'bathtub', 'shower',
    'fireplace', 'chimney'
}

# الأشياء شبه الثابتة (أثاث - يمكن تحريكها لكن عادة ثابتة)
SEMI_FIXED = {
    'chair', 'table', 'desk', 'sofa', 'couch', 'bed', 'wardrobe', 'closet',
    'cabinet', 'shelf', 'bookcase', 'refrigerator', 'fridge', 'oven', 'stove',
    'washing machine', 'dryer', 'tv', 'television', 'monitor', 'lamp',
    'mirror', 'picture', 'frame', 'clock', 'plant', 'vase'
}

# الأشياء المتغيرة/المتحركة
DYNAMIC_OBJECTS = {
    'person', 'man', 'woman', 'child', 'baby', 'kid',
    'cat', 'dog', 'bird', 'animal',
    'car', 'truck', 'bus', 'motorcycle', 'bicycle', 'scooter',
    'ball', 'toy'
}

# الأشياء المفاجئة (قد تكون خطرة)
SURPRISE_OBJECTS = {
    'hole', 'pothole', 'obstacle', 'box', 'bag', 'suitcase',
    'bucket', 'mop', 'broom', 'ladder', 'rope', 'wire', 'cable'
}


@dataclass 
class EnvironmentObject:
    """كائن في البيئة"""
    object_class: str
    object_class_ar: str
    position: str  # 'front', 'left', 'right', etc.
    distance_estimate: float
    first_seen: datetime
    last_seen: datetime
    is_fixed: bool
    confidence: float
    

@dataclass
class BaselineSnapshot:
    """لقطة من البيئة الأساسية"""
    user_id: str
    location_name: str
    objects: Dict[str, EnvironmentObject] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    last_updated: Optional[datetime] = None


class EnvironmentBaseline:
    """
    يدير البيئة الأساسية ويكشف التغييرات
    """
    
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self.data_dir = Path(__file__).parent.parent / 'data' / 'environments'
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.baselines: Dict[str, BaselineSnapshot] = {}
        self.current_location: Optional[str] = None
        
        self._load_baselines()
    
    def _load_baselines(self):
        """تحميل البيئات المحفوظة"""
        user_file = self.data_dir / f'{self.user_id}_baselines.json'
        if user_file.exists():
            try:
                with open(user_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for loc_name, loc_data in data.items():
                        self.baselines[loc_name] = BaselineSnapshot(
                            user_id=self.user_id,
                            location_name=loc_name,
                            created_at=datetime.fromisoformat(loc_data.get('created_at')) if loc_data.get('created_at') else None,
                            last_updated=datetime.fromisoformat(loc_data.get('last_updated')) if loc_data.get('last_updated') else None
                        )
            except Exception as e:
                print(f"⚠️ Error loading baselines: {e}")
    
    def _save_baselines(self):
        """حفظ البيئات"""
        try:
            user_file = self.data_dir / f'{self.user_id}_baselines.json'
            data = {}
            for loc_name, baseline in self.baselines.items():
                data[loc_name] = {
                    'created_at': baseline.created_at.isoformat() if baseline.created_at else None,
                    'last_updated': baseline.last_updated.isoformat() if baseline.last_updated else None,
                    'objects': {
                        key: {
                            'object_class': obj.object_class,
                            'object_class_ar': obj.object_class_ar,
                            'position': obj.position,
                            'distance_estimate': obj.distance_estimate,
                            'is_fixed': obj.is_fixed,
                            'confidence': obj.confidence
                        }
                        for key, obj in baseline.objects.items()
                    }
                }
            with open(user_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving baselines: {e}")
    
    def classify_object(self, obj_class: str) -> str:
        """
        تصنيف الكائن: fixed, semi_fixed, dynamic, surprise
        """
        obj_lower = obj_class.lower()
        
        if obj_lower in ALWAYS_FIXED:
            return 'fixed'
        elif obj_lower in SEMI_FIXED:
            return 'semi_fixed'
        elif obj_lower in DYNAMIC_OBJECTS:
            return 'dynamic'
        elif obj_lower in SURPRISE_OBJECTS:
            return 'surprise'
        else:
            return 'unknown'
    
    def set_location(self, location_name: str) -> Dict:
        """تعيين الموقع الحالي"""
        self.current_location = location_name
        
        if location_name not in self.baselines:
            self.baselines[location_name] = BaselineSnapshot(
                user_id=self.user_id,
                location_name=location_name,
                created_at=datetime.now()
            )
            self._save_baselines()
            return {
                'message': f'موقع جديد: {location_name}. سأتعلم محيطك',
                'is_new': True
            }
        
        return {
            'message': f'مرحباً بك في {location_name}',
            'is_new': False,
            'known_objects': len(self.baselines[location_name].objects)
        }
    
    def update_baseline(self, objects: List[Dict], location_name: str = None) -> Dict:
        """
        تحديث البيئة الأساسية بالأشياء المكتشفة
        """
        loc = location_name or self.current_location
        if not loc:
            return {'error': 'لم يتم تحديد الموقع'}
        
        if loc not in self.baselines:
            self.baselines[loc] = BaselineSnapshot(
                user_id=self.user_id,
                location_name=loc,
                created_at=datetime.now()
            )
        
        baseline = self.baselines[loc]
        now = datetime.now()
        
        for obj in objects:
            obj_class = obj.get('class', 'unknown')
            obj_class_ar = obj.get('class_ar', obj_class)
            classification = self.classify_object(obj_class)
            
            # فقط الأشياء الثابتة وشبه الثابتة تُحفظ في الـ baseline
            if classification in ['fixed', 'semi_fixed']:
                key = f"{obj_class}_{obj.get('position', 'unknown')}"
                
                if key in baseline.objects:
                    # تحديث الكائن الموجود
                    baseline.objects[key].last_seen = now
                    baseline.objects[key].confidence = min(1.0, baseline.objects[key].confidence + 0.1)
                else:
                    # كائن جديد
                    baseline.objects[key] = EnvironmentObject(
                        object_class=obj_class,
                        object_class_ar=obj_class_ar,
                        position=obj.get('position', 'unknown'),
                        distance_estimate=obj.get('distance_m', 0),
                        first_seen=now,
                        last_seen=now,
                        is_fixed=classification == 'fixed',
                        confidence=0.5
                    )
        
        baseline.last_updated = now
        self._save_baselines()
        
        return {
            'location': loc,
            'total_baseline_objects': len(baseline.objects),
            'message': f'تم تحديث البيئة: {len(baseline.objects)} شيء محفوظ'
        }
    
    def detect_changes(self, current_objects: List[Dict], location_name: str = None) -> Dict:
        """
        مقارنة الوضع الحالي مع البيئة الأساسية
        
        Returns:
            dict: {new_objects, missing_objects, surprises, changes_detected}
        """
        loc = location_name or self.current_location
        if not loc or loc not in self.baselines:
            return {
                'changes_detected': False,
                'new_objects': current_objects,
                'missing_objects': [],
                'surprises': [],
                'message': 'لا توجد بيئة أساسية للمقارنة'
            }
        
        baseline = self.baselines[loc]
        
        new_objects = []
        surprises = []
        
        # تصنيف الكائنات الحالية
        current_fixed = set()
        
        for obj in current_objects:
            obj_class = obj.get('class', 'unknown')
            classification = self.classify_object(obj_class)
            
            key = f"{obj_class}_{obj.get('position', 'unknown')}"
            
            if classification == 'surprise':
                surprises.append({
                    **obj,
                    'alert_type': 'surprise',
                    'message': f"تنبيه! {obj.get('class_ar', obj_class)} - شيء غير متوقع"
                })
            elif classification == 'dynamic':
                # الأشياء المتحركة دائماً جديدة (أشخاص، حيوانات)
                new_objects.append({
                    **obj,
                    'alert_type': 'dynamic',
                    'message': f"{obj.get('class_ar', obj_class)} في المحيط"
                })
            elif classification in ['fixed', 'semi_fixed']:
                current_fixed.add(key)
                if key not in baseline.objects:
                    new_objects.append({
                        **obj,
                        'alert_type': 'new_fixed',
                        'message': f"شيء جديد: {obj.get('class_ar', obj_class)}"
                    })
        
        # اكتشاف الأشياء المفقودة
        missing_objects = []
        for key, obj in baseline.objects.items():
            if key not in current_fixed and obj.confidence > 0.7:
                missing_objects.append({
                    'class': obj.object_class,
                    'class_ar': obj.object_class_ar,
                    'position': obj.position,
                    'alert_type': 'missing',
                    'message': f"تغيير: {obj.object_class_ar} غير موجود في مكانه"
                })
        
        # بناء رسالة الملخص
        messages = []
        if surprises:
            messages.append(f"⚠️ {len(surprises)} مفاجآت")
        if new_objects:
            messages.append(f"🆕 {len(new_objects)} أشياء جديدة")
        if missing_objects:
            messages.append(f"❓ {len(missing_objects)} أشياء مفقودة")
        
        changes_detected = len(surprises) > 0 or len(new_objects) > 0 or len(missing_objects) > 0
        
        return {
            'changes_detected': changes_detected,
            'new_objects': new_objects,
            'missing_objects': missing_objects,
            'surprises': surprises,
            'message': ' | '.join(messages) if messages else 'لا توجد تغييرات'
        }
    
    def is_surprise(self, obj: Dict) -> bool:
        """هل هذا الكائن مفاجأة؟"""
        obj_class = obj.get('class', '').lower()
        return obj_class in SURPRISE_OBJECTS
    
    def get_baseline_summary(self, location_name: str = None) -> Dict:
        """ملخص البيئة الأساسية"""
        loc = location_name or self.current_location
        if not loc or loc not in self.baselines:
            return {'error': 'لا توجد بيئة محفوظة'}
        
        baseline = self.baselines[loc]
        
        fixed_count = sum(1 for obj in baseline.objects.values() if obj.is_fixed)
        semi_fixed_count = len(baseline.objects) - fixed_count
        
        return {
            'location': loc,
            'total_objects': len(baseline.objects),
            'fixed_objects': fixed_count,
            'semi_fixed_objects': semi_fixed_count,
            'created_at': baseline.created_at.isoformat() if baseline.created_at else None,
            'last_updated': baseline.last_updated.isoformat() if baseline.last_updated else None
        }


# Instance عام
environment_baseline = EnvironmentBaseline()
