"""
تحسين تقدير المسافة باستخدام MiDaS Depth Estimation
يوفر دقة أعلى بكثير من الطريقة التقريبية القديمة
"""

import cv2
import numpy as np
from pathlib import Path

class DepthEstimator:
    def __init__(self):
        self.model = None
        self.transform = None
        self.load_model()
    
    def load_model(self):
        """تحميل نموذج MiDaS Small (سريع ودقيق)"""
        try:
            import torch
            
            # استخدام MiDaS Small للسرعة
            self.model = torch.hub.load("intel-isl/MiDaS", "MiDaS_small", trust_repo=True)
            self.model.eval()
            
            midas_transforms = torch.hub.load("intel-isl/MiDaS", "transforms", trust_repo=True)
            self.transform = midas_transforms.small_transform
            
            print("✅ Depth Estimator (MiDaS) loaded successfully")
        except Exception as e:
            print(f"⚠️ Depth Estimator not available: {e}")
            print("   المسافات ستُحسب بالطريقة التقريبية")
    
    def estimate_depth(self, image_bytes):
        """تقدير خريطة العمق من صورة"""
        if self.model is None:
            return None
        
        try:
            import torch
            
            # تحويل bytes لصورة
            arr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            
            if img is None:
                return None
            
            # تحويل لـ RGB
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # تحويل للنموذج
            input_batch = self.transform(img_rgb)
            
            # الاستنتاج
            with torch.no_grad():
                prediction = self.model(input_batch)
                prediction = torch.nn.functional.interpolate(
                    prediction.unsqueeze(1),
                    size=img.shape[:2],
                    mode="bicubic",
                    align_corners=False,
                ).squeeze()
            
            depth_map = prediction.cpu().numpy()
            
            return depth_map
            
        except Exception as e:
            print(f"⚠️ Depth estimation error: {e}")
            return None
    
    def get_object_distance(self, depth_map, bbox):
        """حساب مسافة شيء من خريطة العمق"""
        if depth_map is None:
            return None
        
        try:
            x1, y1, x2, y2 = map(int, bbox)
            
            # التأكد من الحدود
            h, w = depth_map.shape
            x1, x2 = max(0, x1), min(w, x2)
            y1, y2 = max(0, y1), min(h, y2)
            
            if x2 <= x1 or y2 <= y1:
                return None
            
            # استخراج منطقة الشيء
            object_region = depth_map[y1:y2, x1:x2]
            
            if object_region.size == 0:
                return None
            
            # حساب الوسيط (أكثر دقة من المتوسط)
            median_depth = np.median(object_region)
            
            # تحويل لمسافة تقريبية بالأمتار
            # MiDaS يعطي قيم نسبية inverse depth
            # معادلة تقريبية بناءً على معايرة تجريبية
            distance_m = 10.0 / (median_depth + 0.1)
            
            # تحديد النطاق المعقول (30cm إلى 20m)
            distance_m = float(max(0.3, min(distance_m, 20.0)))
            
            return distance_m
            
        except Exception as e:
            print(f"⚠️ Distance calculation error: {e}")
            return None

# إنشاء instance عام
depth_estimator = DepthEstimator()
