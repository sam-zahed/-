# YOLO-World v2 - Open Vocabulary Detection
# This model allows defining ANY object class dynamically!
import os
from pathlib import Path
import cv2
import numpy as np
import traceback
from deep_translator import GoogleTranslator

MODELDIR = Path(__file__).resolve().parents[1] / 'models'
MODELDIR.mkdir(parents=True, exist_ok=True)

# Import depth estimator
try:
    from .depth_estimator import depth_estimator
    DEPTH_AVAILABLE = True
except Exception as e:
    print(f"⚠️ Depth estimator not available: {e}")
    depth_estimator = None
    DEPTH_AVAILABLE = False

# Import new FaceRecognizer
try:
    from .face_recognizer import FaceRecognizer
    FACE_REC_AVAILABLE = True
except ImportError:
    print("⚠️ FaceRecognizer module could not be imported.")
    FACE_REC_AVAILABLE = False

# Minimum confidence - Increased to reduce hallucinations
MIN_CONFIDENCE = 0.25 

# Specific thresholds to prevent 'car in bedroom'
CLASS_THRESHOLDS = {
    'car': 0.40,
    'truck': 0.40,
    'bus': 0.40,
    'motorcycle': 0.35,
    'train': 0.40
}

# Custom Vocabulary for Blind Assistance - Expanded
CUSTOM_CLASSES = [
    # Navigation & Hazards (Critical)
    'door', 'open door', 'closed door', 'wooden door', 'glass door', 'white door',
    'stairs', 'staircase', 'steps', 'elevator', 'escalator',
    'hole', 'hole in ground', 'pothole', 'obstacle',
    'wall', 'brick wall', 'concrete wall', 'white wall', 'corner', 'hallway',
    
    # People & Vehicles
    'person', 'child', 'man', 'woman',
    'car', 'truck', 'bus', 'bicycle', 'motorcycle',
    
    # Furniture & Indoor
    'chair', 'armchair', 'wheelchair',
    'table', 'desk', 'dining table',
    'couch', 'sofa', 'bed',
    'tv', 'monitor', 'screen', 'laptop', 'computer',
    'trash can', 'bin',
    'refrigerator', 'fridge',
    'cabinet', 'closet', 'shelf', 'bookcase',
    'sink', 'toilet', 'mirror',
    'lamp', 'light', 'ceiling fan',
    
    # Small Objects
    'keys', 'wallet', 'phone', 'bottle', 'cup', 'glass', 'remote'
]

# Arabic Translations - Robust Mapping
ARABIC_NAMES = {
    'door': 'باب', 'open door': 'باب مفتوح', 'closed door': 'باب مغلق',
    'wooden door': 'باب', 'glass door': 'باب زجاجي', 'white door': 'باب',
    'stairs': 'درج', 'staircase': 'درج', 'steps': 'عوائق', 'elevator': 'مصعد', 'escalator': 'سلم كهربائي',
    'hole': 'حفرة', 'hole in ground': 'حفرة', 'pothole': 'حفرة',
    'obstacle': 'عائق',
    'wall': 'جدار', 'brick wall': 'جدار', 'concrete wall': 'جدار', 'white wall': 'جدار',
    'corner': 'زاوية', 'hallway': 'ممر',
    'person': 'شخص', 'child': 'طفل', 'man': 'رجل', 'woman': 'امرأة',
    'car': 'سيارة', 'truck': 'شاحنة', 'bus': 'باص',
    'bicycle': 'دراجة', 'motorcycle': 'موتور',
    'chair': 'كرسي', 'armchair': 'كرسي', 'wheelchair': 'كرسي متحرك',
    'table': 'طاولة', 'desk': 'مكتب', 'dining table': 'طاولة طعام',
    'couch': 'كنبة', 'sofa': 'كنبة', 'bed': 'سرير',
    'tv': 'شاشة', 'monitor': 'شاشة', 'screen': 'شاشة',
    'laptop': 'لابتوب', 'computer': 'كمبيوتر',
    'trash can': 'سلة مهملات', 'bin': 'سلة',
    'refrigerator': 'ثلاجة', 'fridge': 'ثلاجة',
    'cabinet': 'خزانة', 'closet': 'دولاب',
    'shelf': 'رف', 'bookcase': 'مكتبة',
    'sink': 'مغسلة', 'toilet': 'حمام', 'mirror': 'مرآة',
    'keys': 'مفاتيح', 'wallet': 'محفظة', 'phone': 'جوال',
    'bottle': 'قارورة', 'cup': 'كوب', 'glass': 'كأس', 'remote': 'ريموت',
    'lamp': 'مصباح', 'light': 'إضاءة', 'ceiling fan': 'مروحة سقف'
}

class DummyDetector:
    def detect(self, image_bytes, target_lang='ar'): return []

detector = DummyDetector()

try:
    from ultralytics import YOLO
    
    # Check for YOLO-World model
    world_path = MODELDIR / 'yolov8s-worldv2.pt'
    
    if world_path.exists():
        model = YOLO(str(world_path))
        
        # Set custom classes!
        model.set_classes(CUSTOM_CLASSES)
        
        class WorldDetector:
            def __init__(self, model):
                self.model = model
                self.face_recognizer = FaceRecognizer() if FACE_REC_AVAILABLE else None

            def detect(self, image_bytes, target_lang='ar'):
                # Simple cache for translations to avoid latency
                if not hasattr(self, 'translation_cache'):
                    self.translation_cache = {}

                def get_localized_name(text, lang):
                    key = f"{text}_{lang}"
                    if lang == 'ar' and text in ARABIC_NAMES:
                        return ARABIC_NAMES[text]
                    if key in self.translation_cache:
                        return self.translation_cache[key]
                    try:
                        translated = GoogleTranslator(source='auto', target=lang).translate(text)
                        self.translation_cache[key] = translated
                        return translated
                    except Exception as e:
                        return text

                try:
                    if not image_bytes or len(image_bytes) == 0:
                        return []
                    
                    arr = np.frombuffer(image_bytes, np.uint8)
                    if arr.size == 0: return []
                    
                    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                    if img is None: return []

                    # Resize for performance optimization
                    # Max 640px width
                    h, w = img.shape[:2]
                    if w > 640:
                        scale = 640 / w
                        img = cv2.resize(img, (640, int(h * scale)))
                    
                    # 1. Estimate depth map if available
                    depth_map = None
                    if DEPTH_AVAILABLE and depth_estimator:
                        # Depth estimator expects raw bytes, but we resized the image.
                        # Ideally we should pass the resized image bytes or update logic.
                        # For simplicity, we pass original bytes but this might cause mismatch in coordinates.
                        # Actually, better to skip resize IF depth is critical, or handle scaling coords.
                        # To keep it safe, let's use the original bytes for depth for now or re-encode.
                        # Optimization: We already resized `img`. Let's allow depth estimator to take numpy?
                        # `depth_estimator.estimate_depth` takes bytes.
                        _, encoded_resized = cv2.imencode('.jpg', img)
                        depth_map = depth_estimator.estimate_depth(encoded_resized.tobytes())
                    
                    # 2. Run YOLO-World Inference
                    results = self.model(img, conf=MIN_CONFIDENCE, verbose=False)
                    
                    # 2. Check if we need Face Recognition (if 'person' is detected)
                    has_person = False
                    for r in results:
                        for cls_id in r.boxes.cls:
                            if self.model.names[int(cls_id)] in ['person', 'man', 'woman', 'child']:
                                has_person = True
                                break
                    
                    identified_names = []
                    if has_person and self.face_recognizer:
                        # Convert to RGB for face_recognition
                        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                        identified_names = self.face_recognizer.identify_faces(img_rgb)
                    
                    detections = []
                    for r in results:
                        for box in r.boxes:
                            try:
                                cls_id = int(box.cls[0].item())
                                conf = float(box.conf[0].item())
                                
                                if hasattr(self.model, 'names') and cls_id in self.model.names:
                                    cls_name = self.model.names[cls_id]
                                else:
                                    cls_name = 'unknown'

                                # Dynamic Thresholding
                                if cls_name in CLASS_THRESHOLDS:
                                    if conf < CLASS_THRESHOLDS[cls_name]:
                                        continue

                                # Face Association (Greedy)
                                if cls_name in ['person', 'man', 'woman'] and len(identified_names) > 0:
                                    # Pick the first one
                                    name = identified_names.pop(0)
                                    if name != "Unknown":
                                        cls_name = name

                                localized = get_localized_name(cls_name, target_lang)
                                xyxy = box.xyxy[0].tolist()
                                
                                # Calculate distance
                                dist = 0.0
                                if depth_map is not None and DEPTH_AVAILABLE:
                                    real_dist = depth_estimator.get_object_distance(depth_map, xyxy)
                                    if real_dist:
                                        dist = real_dist
                                
                                if dist == 0.0:
                                    # Heuristic distance estimation
                                    h, w = img.shape[:2]
                                    box_h = xyxy[3] - xyxy[1]
                                    ratio = box_h / h
                                    if ratio > 0.8: dist = 0.5
                                    elif ratio > 0.6: dist = 1.0
                                    elif ratio > 0.4: dist = 2.0
                                    elif ratio > 0.2: dist = 3.5
                                    else: dist = 6.0
                                
                                detections.append({
                                    'class': str(cls_name),
                                    'class_ar': str(localized),
                                    'conf': float(round(conf, 2)),
                                    'bbox': [float(x) for x in xyxy],
                                    'distance_m': float(dist)
                                })
                            except Exception as inner_e:
                                continue
                    
                    detections.sort(key=lambda x: x['distance_m'])
                    return detections[:5]

                except Exception as e:
                    print(f"🔥 CRITICAL INFERENCE ERROR: {e}")
                    traceback.print_exc()
                    return []
        
        detector = WorldDetector(model)
        print(f'✅ YOLO-World loaded classes.')
    else:
        print('⚠️ YOLO-World model not found')

except Exception as e:
    print(f'⚠️ YOLO Error: {e}')

