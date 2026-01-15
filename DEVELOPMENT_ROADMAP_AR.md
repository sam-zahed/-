# 🗺️ خارطة طريق التطوير - نظام مساعدة المكفوفين

## 🎯 الرؤية

تطوير نظام ذكي شامل يمكّن المكفوفين من العيش بشكل مستقل وآمن باستخدام أحدث تقنيات الذكاء الاصطناعي.

---

## 📊 الحالة الحالية للمشروع

### ✅ ما يعمل الآن:
- ✅ كشف الأشياء باستخدام YOLO-World (60+ فئة)
- ✅ ترجمة تلقائية للعربية
- ✅ تقدير المسافة الأساسي
- ✅ التعرف على الوجوه وحفظها
- ✅ تحويل الصوت لنص (Whisper)
- ✅ تحويل النص لصوت (TTS)
- ✅ قاعدة بيانات للأحداث والخرائط
- ✅ WebSocket للاتصال المباشر
- ✅ API كامل مع FastAPI

### ⚠️ ما يحتاج تحسين:
- ⚠️ دقة تقدير المسافة (حالياً تقريبية)
- ⚠️ سرعة الاستجابة (150-500ms)
- ⚠️ دعم اللغة العربية في TTS
- ⚠️ واجهة مستخدم للموبايل
- ⚠️ نظام التنبيهات الصوتية
- ⚠️ الملاحة الداخلية والخارجية

---

## 🚀 المرحلة 1: التحسينات الفورية (أسبوع - شهر)

### 1.1 نظام التنبيهات الصوتية الذكي ⭐⭐⭐

**الأولوية:** عالية جداً  
**الوقت المتوقع:** 3-5 أيام  
**الصعوبة:** متوسطة

**الوصف:**
نظام ينبه المستخدم فوراً بالأخطار حسب الأولوية.

**التنفيذ:**

```python
# ملف جديد: app/alerts/priority_system.py

from enum import Enum
from typing import List, Dict
import asyncio

class AlertPriority(Enum):
    CRITICAL = 1    # خطر فوري (درج، حفرة، سيارة قريبة)
    HIGH = 2        # تحذير مهم (شخص قريب، باب)
    MEDIUM = 3      # معلومة مفيدة (أثاث، أشياء)
    LOW = 4         # معلومة عامة (ألوان، تفاصيل)

PRIORITY_MAP = {
    # أخطار فورية
    'stairs': AlertPriority.CRITICAL,
    'staircase': AlertPriority.CRITICAL,
    'hole': AlertPriority.CRITICAL,
    'pothole': AlertPriority.CRITICAL,
    'escalator': AlertPriority.CRITICAL,
    
    # تحذيرات عالية
    'car': AlertPriority.HIGH,
    'truck': AlertPriority.HIGH,
    'bus': AlertPriority.HIGH,
    'motorcycle': AlertPriority.HIGH,
    'bicycle': AlertPriority.HIGH,
    'door': AlertPriority.HIGH,
    'open door': AlertPriority.HIGH,
    
    # متوسطة
    'person': AlertPriority.MEDIUM,
    'child': AlertPriority.HIGH,  # طفل = أولوية عالية
    'wall': AlertPriority.MEDIUM,
    'obstacle': AlertPriority.MEDIUM,
    
    # منخفضة
    'chair': AlertPriority.LOW,
    'table': AlertPriority.LOW,
}

DISTANCE_MULTIPLIER = {
    # كلما كان الشيء أقرب، زادت الأولوية
    0.5: 3,   # أقل من نصف متر = ضاعف الأولوية 3 مرات
    1.0: 2,   # أقل من متر = ضاعف مرتين
    2.0: 1.5, # أقل من مترين = ضاعف 1.5
    5.0: 1,   # أكثر من 5 أمتار = عادي
}

ARABIC_ALERTS = {
    AlertPriority.CRITICAL: "تحذير خطر!",
    AlertPriority.HIGH: "انتبه!",
    AlertPriority.MEDIUM: "ملاحظة:",
    AlertPriority.LOW: ""
}

DIRECTION_AR = {
    'front': 'أمامك',
    'left': 'على يسارك',
    'right': 'على يمينك',
    'back': 'خلفك'
}

def calculate_direction(bbox, image_width):
    """حساب اتجاه الشيء"""
    center_x = (bbox[0] + bbox[2]) / 2
    
    if center_x < image_width * 0.3:
        return 'left'
    elif center_x > image_width * 0.7:
        return 'right'
    else:
        return 'front'

def get_alert_priority(obj_class: str, distance: float) -> int:
    """حساب أولوية التنبيه"""
    base_priority = PRIORITY_MAP.get(obj_class, AlertPriority.LOW)
    
    # تعديل حسب المسافة
    for dist_threshold, multiplier in sorted(DISTANCE_MULTIPLIER.items()):
        if distance <= dist_threshold:
            priority_value = base_priority.value / multiplier
            return max(1, int(priority_value))
    
    return base_priority.value

def generate_alert_message(detection: Dict, image_width: int) -> Dict:
    """توليد رسالة تنبيه"""
    obj_class = detection['class']
    class_ar = detection.get('class_ar', obj_class)
    distance = detection['distance_m']
    bbox = detection['bbox']
    
    priority_level = get_alert_priority(obj_class, distance)
    priority = AlertPriority(priority_level)
    
    direction = calculate_direction(bbox, image_width)
    direction_ar = DIRECTION_AR[direction]
    
    alert_prefix = ARABIC_ALERTS[priority]
    
    # صياغة الرسالة
    if distance < 1:
        distance_text = f"قريب جداً منك"
    elif distance < 2:
        distance_text = f"على بعد متر {direction_ar}"
    else:
        distance_text = f"على بعد {distance:.0f} متر {direction_ar}"
    
    message = f"{alert_prefix} {class_ar} {distance_text}"
    
    return {
        'priority': priority.value,
        'priority_name': priority.name,
        'message': message,
        'object': class_ar,
        'distance': distance,
        'direction': direction,
        'should_speak': priority.value <= 2  # فقط CRITICAL و HIGH
    }

async def process_detections_with_alerts(detections: List[Dict], image_width: int = 640):
    """معالجة الكشوفات وتوليد التنبيهات"""
    alerts = []
    
    for detection in detections:
        alert = generate_alert_message(detection, image_width)
        alerts.append(alert)
    
    # ترتيب حسب الأولوية
    alerts.sort(key=lambda x: (x['priority'], x['distance']))
    
    # التنبيهات الصوتية (فقط الأهم)
    critical_alerts = [a for a in alerts if a['should_speak']]
    
    return {
        'all_alerts': alerts,
        'critical_alerts': critical_alerts,
        'speak_message': ' . '.join([a['message'] for a in critical_alerts[:3]])  # أهم 3 فقط
    }
```

**دمج في النظام:**

```python
# في app/infer/router.py

from app.alerts.priority_system import process_detections_with_alerts

@router.post('/realtime')
async def realtime_infer(request: InferRequest):
    # ... الكود الحالي ...
    
    # إضافة نظام التنبيهات
    alerts_data = await process_detections_with_alerts(objects, image_width=640)
    
    return {
        "objects": objects,
        "alerts": alerts_data['all_alerts'],
        "speak_message": alerts_data['speak_message'],  # الرسالة الصوتية
        "TTC": 999.0,
        "scene_confidence": 0.8,
        "inference_time_ms": inference_time,
        "model_version": "yolov8-v1"
    }
```

**الفائدة:**
- 🎯 المستخدم يسمع فقط الأهم
- ⚡ استجابة فورية للأخطار
- 🧠 ذكي في ترتيب الأولويات

---

### 1.2 تحسين تقدير المسافة باستخدام Depth Estimation ⭐⭐⭐

**الأولوية:** عالية  
**الوقت المتوقع:** 5-7 أيام  
**الصعوبة:** متوسطة-عالية

**الوصف:**
استخدام نموذج MiDaS أو Depth-Anything لتقدير المسافة الحقيقية.

**التنفيذ:**

```python
# ملف جديد: app/vision/depth_estimator.py

import torch
import cv2
import numpy as np
from pathlib import Path

class DepthEstimator:
    def __init__(self):
        self.model = None
        self.load_model()
    
    def load_model(self):
        """تحميل نموذج MiDaS"""
        try:
            # استخدام MiDaS Small (سريع)
            self.model = torch.hub.load("intel-isl/MiDaS", "MiDaS_small")
            self.model.eval()
            
            self.transform = torch.hub.load("intel-isl/MiDaS", "transforms").small_transform
            
            print("✅ Depth Estimator loaded")
        except Exception as e:
            print(f"⚠️ Depth Estimator failed: {e}")
    
    def estimate_depth(self, image_bytes):
        """تقدير العمق من صورة"""
        if self.model is None:
            return None
        
        try:
            # تحويل bytes لصورة
            arr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
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
            
            # استخراج منطقة الشيء
            object_region = depth_map[y1:y2, x1:x2]
            
            # حساب المتوسط (أو الوسيط للدقة)
            median_depth = np.median(object_region)
            
            # تحويل لمسافة تقريبية بالأمتار
            # MiDaS يعطي قيم نسبية، نحتاج معايرة
            # هذه معادلة تقريبية
            distance_m = 10.0 / (median_depth + 1.0)
            
            return max(0.3, min(distance_m, 20.0))  # بين 30cm و 20m
            
        except Exception as e:
            print(f"⚠️ Distance calculation error: {e}")
            return None

# إنشاء instance عام
depth_estimator = DepthEstimator()
```

**الدمج:**

```python
# في app/vision/model.py

from .depth_estimator import depth_estimator

class WorldDetector:
    def detect(self, image_bytes):
        # ... الكود الحالي ...
        
        # تقدير العمق
        depth_map = depth_estimator.estimate_depth(image_bytes)
        
        for box in r.boxes:
            # ... الكود الحالي ...
            
            # استخدام العمق الحقيقي إذا متاح
            if depth_map is not None:
                real_distance = depth_estimator.get_object_distance(depth_map, xyxy)
                if real_distance:
                    dist = real_distance
            else:
                # الطريقة القديمة كـ fallback
                # ... الكود الحالي ...
```

**الفائدة:**
- 📏 دقة أعلى بكثير في المسافات
- 🎯 تحذيرات أكثر موثوقية
- 🚀 يعمل في أي بيئة

---

### 1.3 واجهة موبايل بسيطة (PWA) ⭐⭐

**الأولوية:** متوسطة-عالية  
**الوقت المتوقع:** 3-5 أيام  
**الصعوبة:** متوسطة

**الوصف:**
تطبيق ويب تقدمي (PWA) يعمل على أي موبايل بدون تثبيت.

**التنفيذ:**

```html
<!-- ملف جديد: client/index.html -->

<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>مساعد المكفوفين</title>
    <link rel="manifest" href="/manifest.json">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #1a1a1a;
            color: white;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        #video-container {
            flex: 1;
            position: relative;
            background: black;
        }
        #camera-feed {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        #overlay {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
        }
        #controls {
            padding: 20px;
            background: #2a2a2a;
            display: flex;
            gap: 10px;
            justify-content: center;
        }
        button {
            padding: 15px 30px;
            font-size: 18px;
            border: none;
            border-radius: 10px;
            background: #4CAF50;
            color: white;
            cursor: pointer;
            font-weight: bold;
        }
        button:active { background: #45a049; }
        button.danger { background: #f44336; }
        #status {
            padding: 10px;
            text-align: center;
            background: #333;
            font-size: 16px;
        }
        .alert-critical {
            background: #f44336 !important;
            animation: pulse 0.5s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
    </style>
</head>
<body>
    <div id="status">جاهز للبدء</div>
    
    <div id="video-container">
        <video id="camera-feed" autoplay playsinline></video>
        <canvas id="overlay"></canvas>
    </div>
    
    <div id="controls">
        <button id="start-btn" onclick="startAssistant()">ابدأ</button>
        <button id="stop-btn" onclick="stopAssistant()" class="danger" style="display:none">أوقف</button>
    </div>

    <script>
        const API_URL = window.location.origin;
        let stream = null;
        let intervalId = null;
        let synth = window.speechSynthesis;
        
        async function startAssistant() {
            try {
                // طلب الكاميرا
                stream = await navigator.mediaDevices.getUserMedia({
                    video: { facingMode: 'environment' }
                });
                
                document.getElementById('camera-feed').srcObject = stream;
                document.getElementById('start-btn').style.display = 'none';
                document.getElementById('stop-btn').style.display = 'block';
                document.getElementById('status').textContent = 'يعمل الآن...';
                
                // بدء التحليل كل ثانية
                intervalId = setInterval(analyzeFrame, 1000);
                
                speak('بدأ المساعد');
                
            } catch (err) {
                alert('خطأ في الوصول للكاميرا: ' + err.message);
            }
        }
        
        function stopAssistant() {
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
            }
            if (intervalId) {
                clearInterval(intervalId);
            }
            
            document.getElementById('start-btn').style.display = 'block';
            document.getElementById('stop-btn').style.display = 'none';
            document.getElementById('status').textContent = 'متوقف';
            
            speak('توقف المساعد');
        }
        
        async function analyzeFrame() {
            const video = document.getElementById('camera-feed');
            const canvas = document.createElement('canvas');
            canvas.width = 640;
            canvas.height = 480;
            
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0, 640, 480);
            
            // تحويل لـ base64
            const imageData = canvas.toDataURL('image/jpeg', 0.8);
            
            try {
                const response = await fetch(`${API_URL}/infer/realtime`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        event_id: Date.now().toString(),
                        user_id: 'mobile_user',
                        small_image_b64: imageData
                    })
                });
                
                const result = await response.json();
                
                // رسم النتائج
                drawDetections(result.objects);
                
                // التنبيه الصوتي
                if (result.speak_message) {
                    speak(result.speak_message);
                }
                
                // تحديث الحالة
                updateStatus(result);
                
            } catch (err) {
                console.error('Analysis error:', err);
            }
        }
        
        function drawDetections(objects) {
            const canvas = document.getElementById('overlay');
            const video = document.getElementById('camera-feed');
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            
            const ctx = canvas.getContext('2d');
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            objects.forEach(obj => {
                const [x1, y1, x2, y2] = obj.bbox;
                
                // لون حسب المسافة
                let color = 'green';
                if (obj.distance_m < 1) color = 'red';
                else if (obj.distance_m < 2) color = 'orange';
                
                ctx.strokeStyle = color;
                ctx.lineWidth = 3;
                ctx.strokeRect(x1, y1, x2-x1, y2-y1);
                
                // النص
                ctx.fillStyle = color;
                ctx.font = '20px Arial';
                ctx.fillText(`${obj.class} (${obj.distance_m.toFixed(1)}m)`, x1, y1-5);
            });
        }
        
        function speak(text) {
            // إيقاف الكلام السابق
            synth.cancel();
            
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = 'ar-SA';
            utterance.rate = 1.1;
            utterance.pitch = 1.0;
            
            synth.speak(utterance);
        }
        
        function updateStatus(result) {
            const status = document.getElementById('status');
            const criticalObjects = result.objects.filter(o => o.distance_m < 1.5);
            
            if (criticalObjects.length > 0) {
                status.className = 'alert-critical';
                status.textContent = `⚠️ ${criticalObjects.length} أشياء قريبة!`;
            } else {
                status.className = '';
                status.textContent = `${result.objects.length} أشياء مكتشفة`;
            }
        }
    </script>
</body>
</html>
```

**الفائدة:**
- 📱 يعمل على أي موبايل فوراً
- 🎤 تنبيهات صوتية تلقائية
- 👁️ واجهة بصرية للمبصرين المساعدين

---

## 🌟 المرحلة 2: ميزات متقدمة (1-3 أشهر)

### 2.1 التعرف على النصوص (OCR) ⭐⭐⭐

**الأهمية:** عالية جداً للحياة اليومية

**الاستخدامات:**
- قراءة اللافتات
- أسماء المحلات
- تواريخ الصلاحية
- أرقام الحافلات
- القوائم في المطاعم
- الأدوية

**التنفيذ:**

```python
# ملف جديد: app/vision/ocr_reader.py

import easyocr
from typing import List, Dict

class OCRReader:
    def __init__(self):
        # دعم العربية والإنجليزية
        self.reader = easyocr.Reader(['ar', 'en'], gpu=False)
        print("✅ OCR Reader loaded (Arabic + English)")
    
    def read_text(self, image_bytes) -> List[Dict]:
        """قراءة النصوص من صورة"""
        try:
            import cv2
            import numpy as np
            
            arr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            
            # قراءة النصوص
            results = self.reader.readtext(img)
            
            texts = []
            for (bbox, text, confidence) in results:
                if confidence > 0.3:  # فقط النصوص الواضحة
                    texts.append({
                        'text': text,
                        'confidence': round(confidence, 2),
                        'bbox': bbox,
                        'language': 'ar' if self._is_arabic(text) else 'en'
                    })
            
            return texts
            
        except Exception as e:
            print(f"⚠️ OCR error: {e}")
            return []
    
    def _is_arabic(self, text):
        """كشف إذا كان النص عربي"""
        arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
        return arabic_chars > len(text) / 2

ocr_reader = OCRReader()
```

**endpoint جديد:**

```python
# في app/vision/router.py

@router.post('/read_text')
async def read_text(file: UploadFile = File(...)):
    """قراءة النصوص من صورة"""
    content = await file.read()
    texts = ocr_reader.read_text(content)
    
    # تجميع النصوص
    all_text = ' . '.join([t['text'] for t in texts])
    
    return {
        'texts': texts,
        'combined_text': all_text,
        'count': len(texts)
    }
```

---

### 2.2 التعرف على العملات والنقود ⭐⭐

**الأهمية:** عالية للاستقلالية المالية

**التنفيذ:**
- تدريب نموذج YOLO على العملات المحلية
- كشف الفئات (1، 5، 10، 20، 50، 100، 200)
- التمييز بين الورقي والمعدني

---

### 2.3 وضع التسوق الذكي ⭐⭐

**الميزات:**
- مسح الباركود
- قراءة الأسعار
- التعرف على المنتجات
- تحذير من تواريخ الصلاحية

---

### 2.4 الملاحة الداخلية ⭐⭐⭐

**الوصف:**
بناء خريطة 3D للأماكن المألوفة (البيت، المكتب).

**التقنيات:**
- SLAM (Simultaneous Localization and Mapping)
- ARCore/ARKit للموبايل
- حفظ المعالم الثابتة

---

## 🚀 المرحلة 3: الذكاء المتقدم (3-6 أشهر)

### 3.1 الذكاء الاصطناعي التحادثي ⭐⭐⭐

**الوصف:**
دمج GPT-4 أو Claude للإجابة على الأسئلة المعقدة.

**أمثلة:**
- "ماذا أمامي؟" → وصف تفصيلي
- "كيف أصل للباب؟" → إرشادات خطوة بخطوة
- "هل هذا آمن؟" → تحليل المخاطر

---

### 3.2 التعلم المستمر والتخصيص ⭐⭐

**الميزات:**
- تعلم عادات المستخدم
- تذكر الأماكن المفضلة
- توقع الاحتياجات
- التكيف مع البيئة

---

### 3.3 الملاحة الخارجية بـ GPS ⭐⭐⭐

**الميزات:**
- دمج مع Google Maps
- إرشادات صوتية خطوة بخطوة
- كشف إشارات المرور
- تحذير من المركبات

---

## 📊 مقاييس النجاح

### المقاييس التقنية:
- ✅ دقة الكشف: > 90%
- ✅ سرعة الاستجابة: < 300ms
- ✅ دقة المسافة: ± 20cm
- ✅ معدل الأخطاء: < 5%

### المقاييس البشرية:
- ✅ رضا المستخدمين: > 85%
- ✅ الاستخدام اليومي: > 70%
- ✅ الحوادث المتجنبة: قياس كمي
- ✅ الاستقلالية: زيادة ملموسة

---

## 🎓 الخلاصة

هذا المشروع لديه إمكانيات هائلة لتغيير حياة المكفوفين. الأولويات:

1. **نظام التنبيهات الصوتية** - فوري وحيوي
2. **تحسين المسافة بـ Depth** - دقة أعلى
3. **واجهة موبايل PWA** - سهولة الاستخدام
4. **OCR للنصوص** - ضروري للحياة اليومية
5. **الملاحة الداخلية** - استقلالية في الأماكن المألوفة

**التركيز:** السلامة أولاً، ثم الاستقلالية، ثم الراحة.

**المبدأ:** كل ميزة يجب أن تُختبر مع مستخدمين حقيقيين قبل الإطلاق.
