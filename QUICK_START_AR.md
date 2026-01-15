# 🚀 دليل البدء السريع - نظام مساعدة المكفوفين

## 📋 المتطلبات الأساسية

### 1. البرامج المطلوبة:
- **Docker** و **Docker Compose** (الطريقة الموصى بها)
- أو **Python 3.11+** للتشغيل المباشر

### 2. المساحة المطلوبة:
- **5 GB** لنماذج الذكاء الاصطناعي
- **2 GB** للـ Docker images
- **1 GB** لقاعدة البيانات

---

## ⚡ التشغيل السريع (5 دقائق)

### الخطوة 1️⃣: تحميل النماذج

```bash
# في مجلد المشروع
cd /home/samoushi/Code/ABDO/fastapi_agent_full_package_with_models_B/fastapi_agent_full_package

# تحميل YOLO-World و Whisper
chmod +x download_models.sh
./download_models.sh
```

**ماذا يحدث؟**
- يحمل نموذج YOLO-World v2 (~338 MB) للكشف عن الأشياء
- يحمل نموذج Whisper Base (~150 MB) لتحويل الصوت لنص

### الخطوة 2️⃣: تشغيل النظام

```bash
# تشغيل جميع الخدمات
docker compose up --build
```

**انتظر حتى ترى:**
```
✅ YOLO-World loaded with custom vocabulary
INFO: Uvicorn running on http://0.0.0.0:8000
```

### الخطوة 3️⃣: اختبار النظام

افتح المتصفح على: **http://localhost:8000**

يجب أن ترى:
```json
{
  "status": "ok",
  "message": "Go to /client for the accessible interface"
}
```

---

## 🧪 اختبار الميزات الأساسية

### 1️⃣ اختبار الكشف عن الأشياء

```bash
# التقط صورة أو استخدم صورة موجودة
curl -X POST http://localhost:8000/vision/detect \
  -F "file=@test_image.jpg"
```

**النتيجة المتوقعة:**
```json
{
  "detections": [
    {
      "class": "door",
      "class_ar": "باب",
      "conf": 0.85,
      "distance_m": 2.0,
      "bbox": [100, 150, 300, 450]
    }
  ]
}
```

### 2️⃣ اختبار الاستنتاج في الوقت الفعلي

```bash
# تحويل صورة لـ base64
BASE64_IMAGE=$(base64 -w 0 test_image.jpg)

# إرسال للـ API
curl -X POST http://localhost:8000/infer/realtime \
  -H "Content-Type: application/json" \
  -d "{
    \"event_id\": \"test_$(date +%s)\",
    \"user_id\": \"test_user\",
    \"small_image_b64\": \"$BASE64_IMAGE\"
  }"
```

**النتيجة المتوقعة:**
```json
{
  "objects": [
    {
      "class": "person",
      "confidence": 0.92,
      "distance_m": 3.5,
      "bbox": [200, 100, 400, 500]
    }
  ],
  "TTC": 999.0,
  "scene_confidence": 0.8,
  "inference_time_ms": 150
}
```

### 3️⃣ اختبار تحويل الصوت لنص

```bash
# سجل ملف صوتي أو استخدم ملف موجود
curl -X POST http://localhost:8000/audio/asr \
  -F "file=@test_audio.mp3"
```

**النتيجة المتوقعة:**
```json
{
  "text": "مرحبا كيف حالك"
}
```

### 4️⃣ اختبار تحويل النص لصوت

```bash
curl -X POST http://localhost:8000/audio/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "مرحبا بك في النظام"}' \
  --output output.wav
```

**النتيجة:** ملف صوتي `output.wav`

---

## 🎯 السيناريوهات العملية

### السيناريو 1: التعرف على الأشياء أمامك

**الخطوات:**
1. التقط صورة بالكاميرا
2. أرسلها لـ `/infer/realtime`
3. استمع للنتيجة

**كود Python:**
```python
import requests
import base64
from pathlib import Path

# قراءة الصورة
image_path = "current_view.jpg"
with open(image_path, "rb") as f:
    image_b64 = base64.b64encode(f.read()).decode()

# إرسال للـ API
response = requests.post(
    "http://localhost:8000/infer/realtime",
    json={
        "event_id": "view_001",
        "user_id": "user123",
        "small_image_b64": image_b64
    }
)

# معالجة النتيجة
result = response.json()
for obj in result["objects"]:
    print(f"{obj['class_ar']} على بعد {obj['distance_m']} متر")
    # يمكنك تحويل هذا لصوت باستخدام /audio/tts
```

### السيناريو 2: تعلم وجه شخص جديد

**الخطوات:**
1. التقط صورة للشخص
2. سجل صوتك وأنت تقول اسمه
3. أرسلهما معاً لـ `/interactive/learn`

**كود Python:**
```python
import requests
import base64

# قراءة الصورة
with open("person_photo.jpg", "rb") as f:
    image_b64 = base64.b64encode(f.read()).decode()

# قراءة الصوت
with open("name_audio.mp3", "rb") as f:
    audio_data = f.read()

# إرسال للـ API
response = requests.post(
    "http://localhost:8000/interactive/learn",
    data={"image": f"data:image/jpeg;base64,{image_b64}"},
    files={"audio": ("audio.mp3", audio_data, "audio/mpeg")}
)

result = response.json()
print(result["message"])  # "Learned: أحمد"
```

### السيناريو 3: البحث عن شيء مفقود

**الخطوات:**
1. استعلم عن آخر مرة شوهد فيها الشيء
2. راجع السجلات في قاعدة البيانات

**كود Python:**
```python
import requests

# البحث في السجلات
response = requests.get(
    "http://localhost:8000/events/search",
    params={
        "object_class": "keys",  # مفاتيح
        "limit": 10
    }
)

events = response.json()
if events:
    last_seen = events[0]
    print(f"شوهدت آخر مرة: {last_seen['timestamp_utc']}")
    print(f"الموقع: {last_seen['location']}")
```

---

## 🔧 إعدادات متقدمة

### تخصيص الكلمات المكتشفة

عدّل `app/vision/model.py`:

```python
CUSTOM_CLASSES = [
    # أضف كلماتك الخاصة هنا
    'door', 'stairs', 'person',
    'medicine bottle',  # زجاجة دواء
    'prayer mat',       # سجادة صلاة
    'quran',           # مصحف
    # ... إلخ
]

# أضف الترجمات
ARABIC_NAMES = {
    'medicine bottle': 'زجاجة دواء',
    'prayer mat': 'سجادة صلاة',
    'quran': 'مصحف',
}
```

### تعديل حد الثقة

عدّل `app/vision/model.py`:

```python
MIN_CONFIDENCE = 0.10  # القيمة الحالية (يكتشف كل شيء)
MIN_CONFIDENCE = 0.50  # قيمة متوسطة (أكثر دقة)
MIN_CONFIDENCE = 0.70  # قيمة عالية (دقة عالية جداً)
```

### تغيير اللغة الافتراضية

عدّل `app/audio/tts.py`:

```python
# للعربية
engine.setProperty('voice', 'arabic')

# للإنجليزية
engine.setProperty('voice', 'english')
```

---

## 📱 التكامل مع تطبيق موبايل

### مثال Flutter/Dart:

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:image_picker/image_picker.dart';

Future<void> analyzeCurrentView() async {
  // 1. التقاط صورة
  final picker = ImagePicker();
  final image = await picker.pickImage(source: ImageSource.camera);
  
  if (image == null) return;
  
  // 2. تحويل لـ base64
  final bytes = await image.readAsBytes();
  final base64Image = base64Encode(bytes);
  
  // 3. إرسال للـ API
  final response = await http.post(
    Uri.parse('http://YOUR_SERVER_IP:8000/infer/realtime'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({
      'event_id': DateTime.now().millisecondsSinceEpoch.toString(),
      'user_id': 'user123',
      'small_image_b64': base64Image,
    }),
  );
  
  // 4. معالجة النتيجة
  final result = jsonDecode(response.body);
  
  // 5. تحويل لصوت
  String announcement = '';
  for (var obj in result['objects']) {
    announcement += '${obj['class_ar']} على بعد ${obj['distance_m']} متر. ';
  }
  
  // 6. تشغيل الصوت
  await speak(announcement);
}

Future<void> speak(String text) async {
  // استخدم مكتبة TTS في Flutter
  // أو أرسل لـ /audio/tts
  final response = await http.post(
    Uri.parse('http://YOUR_SERVER_IP:8000/audio/tts'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({'text': text}),
  );
  
  // شغل الصوت المستلم
  // ...
}
```

### مثال React Native:

```javascript
import { Camera } from 'expo-camera';
import * as Speech from 'expo-speech';

async function analyzeCurrentView() {
  // 1. التقاط صورة
  const photo = await camera.takePictureAsync({ base64: true });
  
  // 2. إرسال للـ API
  const response = await fetch('http://YOUR_SERVER_IP:8000/infer/realtime', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      event_id: Date.now().toString(),
      user_id: 'user123',
      small_image_b64: photo.base64,
    }),
  });
  
  const result = await response.json();
  
  // 3. تحويل لصوت
  let announcement = '';
  result.objects.forEach(obj => {
    announcement += `${obj.class_ar} على بعد ${obj.distance_m} متر. `;
  });
  
  // 4. تشغيل الصوت
  Speech.speak(announcement, { language: 'ar' });
}
```

---

## 🐛 حل المشاكل الشائعة

### المشكلة 1: النظام لا يبدأ

**الحل:**
```bash
# تحقق من Docker
docker --version
docker compose --version

# تحقق من المنافذ
sudo netstat -tulpn | grep -E '8000|5432|9000'

# أعد تشغيل Docker
docker compose down
docker compose up --build
```

### المشكلة 2: النماذج لم تُحمّل

**الحل:**
```bash
# تحقق من وجود النماذج
ls -lh app/models/

# إعادة التحميل
rm -rf app/models/*
./download_models.sh
```

### المشكلة 3: الكشف غير دقيق

**الحل:**
```python
# زد حد الثقة في app/vision/model.py
MIN_CONFIDENCE = 0.50  # بدلاً من 0.10

# أو أضف كلمات أكثر تحديداً
CUSTOM_CLASSES = [
    'wooden door',      # بدلاً من 'door'
    'metal stairs',     # بدلاً من 'stairs'
]
```

### المشكلة 4: بطء في الاستجابة

**الحل:**
```python
# قلل حجم الصورة قبل الإرسال
from PIL import Image

img = Image.open('photo.jpg')
img.thumbnail((640, 480))  # تصغير
img.save('photo_small.jpg')

# أو استخدم GPU إذا متاح
# في docker-compose.yml:
# deploy:
#   resources:
#     reservations:
#       devices:
#         - driver: nvidia
#           count: 1
#           capabilities: [gpu]
```

---

## 📊 مراقبة الأداء

### عرض السجلات:

```bash
# سجلات FastAPI
docker logs -f fastapi_agent_full_package-fastapi-1

# سجلات قاعدة البيانات
docker logs -f fastapi_agent_full_package-postgres-1

# سجلات n8n
docker logs -f fastapi_agent_full_package-n8n-1
```

### فحص قاعدة البيانات:

```bash
# الدخول لـ PostgreSQL
docker exec -it fastapi_agent_full_package-postgres-1 psql -U postgres -d fastapi_agent

# عرض الجداول
\dt

# عرض آخر 10 أحداث
SELECT * FROM events ORDER BY created_at DESC LIMIT 10;

# عرض الخريطة
SELECT * FROM map_features;
```

### قياس الأداء:

```python
import time
import requests

def benchmark_inference():
    """قياس سرعة الاستنتاج"""
    with open('test.jpg', 'rb') as f:
        image_b64 = base64.b64encode(f.read()).decode()
    
    times = []
    for i in range(10):
        start = time.time()
        response = requests.post(
            'http://localhost:8000/infer/realtime',
            json={
                'event_id': f'bench_{i}',
                'user_id': 'test',
                'small_image_b64': image_b64
            }
        )
        elapsed = time.time() - start
        times.append(elapsed)
        print(f"Request {i+1}: {elapsed:.2f}s")
    
    print(f"\nAverage: {sum(times)/len(times):.2f}s")
    print(f"Min: {min(times):.2f}s")
    print(f"Max: {max(times):.2f}s")

benchmark_inference()
```

---

## 🎓 الخطوات التالية

### للمطورين:
1. اقرأ `PROJECT_OVERVIEW_AR.md` للفهم الشامل
2. راجع `docs/` للتفاصيل التقنية
3. جرب إضافة ميزة جديدة (مثل كشف الألوان)
4. شارك تحسيناتك مع المجتمع

### للمستخدمين:
1. جرب النظام في بيئات مختلفة
2. سجل الأخطاء والملاحظات
3. اقترح ميزات جديدة
4. ساعد في تحسين دقة النماذج

### للباحثين:
1. اجمع بيانات حقيقية من مستخدمين مكفوفين
2. قيّم دقة النظام في سيناريوهات مختلفة
3. طوّر نماذج أفضل للغة العربية
4. انشر النتائج لمساعدة المجتمع

---

## 📞 الدعم والمساعدة

- **الوثائق:** `docs/` في المشروع
- **الأمثلة:** `n8n_templates/` و `function_snippets/`
- **الأسئلة:** افتح Issue على GitHub
- **المساهمة:** أرسل Pull Request

---

**تذكر:** هذا النظام يمكن أن يغير حياة شخص كفيف. كل تحسين صغير يمكن أن يحدث فرقاً كبيراً! 💙
