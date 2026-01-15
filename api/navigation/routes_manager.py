"""
نظام حفظ المسارات المعتادة للكفيف
يحفظ المسارات المتكررة ويعطي تنبيهات مخصصة
"""

from typing import Dict, List, Optional
from datetime import datetime
import json
from pathlib import Path

class RouteManager:
    def __init__(self):
        self.routes_file = Path(__file__).parent / 'saved_routes.json'
        self.routes = self.load_routes()
        self.current_route = None
        self.route_history = []
    
    def load_routes(self) -> Dict:
        """تحميل المسارات المحفوظة"""
        if self.routes_file.exists():
            try:
                with open(self.routes_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_routes(self):
        """حفظ المسارات"""
        try:
            with open(self.routes_file, 'w', encoding='utf-8') as f:
                json.dump(self.routes, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving routes: {e}")
    
    def add_route(self, route_name: str, description: str = ""):
        """إضافة مسار جديد"""
        if route_name not in self.routes:
            self.routes[route_name] = {
                'name': route_name,
                'description': description,
                'landmarks': [],
                'warnings': [],
                'created_at': datetime.now().isoformat(),
                'usage_count': 0
            }
            self.save_routes()
            return True
        return False
    
    def add_landmark(self, route_name: str, landmark: Dict):
        """إضافة علامة مميزة للمسار"""
        if route_name in self.routes:
            self.routes[route_name]['landmarks'].append({
                'object': landmark.get('object', ''),
                'object_ar': landmark.get('object_ar', ''),
                'position': landmark.get('position', 'unknown'),
                'distance': landmark.get('distance', 0),
                'timestamp': datetime.now().isoformat()
            })
            self.save_routes()
    
    def add_warning(self, route_name: str, warning: str):
        """إضافة تحذير للمسار"""
        if route_name in self.routes:
            if warning not in self.routes[route_name]['warnings']:
                self.routes[route_name]['warnings'].append(warning)
                self.save_routes()
    
    def start_route(self, route_name: str):
        """بدء مسار"""
        if route_name in self.routes:
            self.current_route = route_name
            self.routes[route_name]['usage_count'] += 1
            self.routes[route_name]['last_used'] = datetime.now().isoformat()
            self.save_routes()
            return self.routes[route_name]
        return None
    
    def get_route_guidance(self, route_name: str, current_objects: List[Dict]) -> Optional[str]:
        """الحصول على إرشادات للمسار الحالي"""
        if route_name not in self.routes:
            return None
        
        route = self.routes[route_name]
        
        # التحقق من العلامات المميزة
        for landmark in route['landmarks']:
            for obj in current_objects:
                if obj.get('object_ar') == landmark['object_ar']:
                    return f"أنت على المسار الصحيح، {landmark['object_ar']} {landmark['position']}"
        
        # التحقق من التحذيرات
        for warning in route['warnings']:
            return f"تذكير: {warning}"
        
        return None
    
    def list_routes(self) -> List[Dict]:
        """قائمة جميع المسارات"""
        return list(self.routes.values())

# Instance عام
route_manager = RouteManager()
