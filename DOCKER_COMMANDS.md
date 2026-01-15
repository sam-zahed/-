# 🐳 أوامر Docker الأساسية - الدليل السريع

## 🚀 البدء السريع (نقطة البداية)

```bash
# 1️⃣ البدء الأول (مع البناء)
docker-compose up --build

# 2️⃣ انتظر 30-60 ثانية حتى تبدأ جميع الخدمات
# ستشاهد: "fastapi | Uvicorn running on http://0.0.0.0:8000"

# 3️⃣ افتح في المتصفح
http://localhost:8000/client/

# 4️⃣ جرّب قول شيء ما:
# "مرحبا" أو "ماذا أمامي؟"
```

---

## 🔄 الأوامر الشائعة

### ▶️ التشغيل

```bash
# بدء عادي (بدون بناء):
docker-compose up

# بدء في الخلفية (بدون رؤية السجلات):
docker-compose up -d

# بدء مع إعادة بناء:
docker-compose up --build

# بدء خدمة واحدة فقط:
docker-compose up fastapi
docker-compose up postgres
docker-compose up minio
docker-compose up ollama
```

### ⏹️ الإيقاف

```bash
# إيقاف الخدمات (الأمر Ctrl+C إذا كان في المقدمة):
docker-compose stop

# إيقاف وحذف الحاويات:
docker-compose down

# إيقاف وحذف كل شيء (حتى البيانات!):
docker-compose down -v

# إيقاف خدمة واحدة:
docker-compose stop fastapi
```

### 🔍 المراقبة

```bash
# شاهد حالة الخدمات:
docker-compose ps

# شاهد السجلات (جميع الخدمات):
docker-compose logs -f

# شاهد آخر 50 سطر:
docker-compose logs --tail=50

# شاهد السجلات لخدمة معينة:
docker-compose logs -f fastapi
docker-compose logs -f postgres
docker-compose logs -f minio

# شاهد السجلات من وقت معين:
docker-compose logs --since 10m fastapi
```

### 🔧 الإعادة والإصلاح

```bash
# إعادة تشغيل خدمة:
docker-compose restart fastapi

# إعادة بناء صورة:
docker-compose build fastapi
docker-compose build --no-cache fastapi  # إعادة كاملة

# إعادة كاملة (حذف وبناء):
docker-compose down -v
docker-compose up --build

# تحديث الخدمات:
docker-compose up -d --pull always
```

### 🖥️ الوصول للحاوية

```bash
# فتح terminal داخل FastAPI:
docker-compose exec fastapi bash

# فتح Python shell:
docker-compose exec fastapi python

# تنفيذ أمر مباشر:
docker-compose exec fastapi python app/download_models.py
docker-compose exec fastapi pip install package_name

# الوصول إلى PostgreSQL:
docker-compose exec postgres psql -U postgres -d fastapi_agent

# الوصول إلى MinIO:
docker-compose exec minio bash
```

### 📊 حالة الموارد

```bash
# عرض استهلاك CPU و Memory:
docker stats

# معلومات فصيلة عن حاوية:
docker inspect blind_assist_api
docker inspect blind_assist_db

# حجم الصور:
docker images | grep blind

# حجم الحاويات:
docker ps -a --format "{{.Names}}\t{{.Size}}"
```

### 🧹 التنظيف

```bash
# حذف الحاويات المتوقفة:
docker-compose down

# حذف الصور:
docker-compose down --rmi local

# حذف كل شيء (بيانات أيضاً):
docker-compose down -v

# تنظيف عام (حذف ما لا يستخدم):
docker system prune -a --volumes
```

---

## 🌐 الوصول للخدمات

### الواجهة الرئيسية
```
http://localhost:8000/client/
```

### Swagger Documentation
```
http://localhost:8000/docs
```

### API مباشر
```
curl http://localhost:8000/health

# النتيجة:
{"status":"healthy","service":"smart-blind-assistant"}
```

### MinIO Console
```
http://localhost:9001
المستخدم: minioadmin
كلمة المرور: minioadmin
```

### Ollama
```
curl http://localhost:11434/api/tags
```

### PostgreSQL
```bash
docker-compose exec postgres psql -U postgres
```

---

## 🧪 الاختبارات

### اختبار الاتصال:

```bash
# اختبر FastAPI:
curl http://localhost:8000/

# اختبر الصحة:
curl http://localhost:8000/health

# اختبر Vision API:
curl -X POST http://localhost:8000/vision/health

# اختبر Audio API:
curl -X POST http://localhost:8000/audio/health

# اختبر Database:
docker-compose exec postgres pg_isready -U postgres

# اختبر Storage:
curl http://localhost:9000/minio/health/live

# اختبر LLM:
docker-compose exec ollama ollama list
```

### اختبار شامل:

```bash
# شغّل test suite:
docker-compose exec fastapi python test_phases.py

# شاهد النتائج:
docker-compose logs fastapi | grep "PASSED\|FAILED"
```

---

## 🔐 الإعدادات والمتغيرات

### عرض المتغيرات الحالية:

```bash
# عرض البيئة الكاملة:
docker-compose config

# عرض بيئة خدمة معينة:
docker-compose config | grep -A 10 "environment"
```

### تغيير المتغيرات:

```bash
# في docker-compose.yml، عدّل:
environment:
  - DATABASE_URL=postgresql://user:password@postgres:5432/db
  - MINIO_ENDPOINT=minio:9000
  - OLLAMA_HOST=http://ollama:11434
```

ثم:
```bash
docker-compose down
docker-compose up --build
```

---

## 📝 ملفات مهمة

### الملفات الأساسية:
```
docker-compose.yml        → إعدادات الخدمات
app/Dockerfile           → بناء صورة FastAPI
requirements.txt         → المكتبات Python
app/main.py              → تطبيق FastAPI
```

### الملفات المساعدة:
```
.env (اختياري)           → متغيرات البيئة
docker-compose.override.yml (اختياري) → إعدادات محلية
```

---

## 💾 حفظ واستعادة البيانات

### حفظ البيانات:

```bash
# حفظ قاعدة البيانات:
docker-compose exec postgres pg_dump -U postgres fastapi_agent > backup.sql

# حفظ التخزين:
docker cp blind_assist_storage:/data ./minio_backup

# حفظ كل البيانات:
docker-compose down
cp -r pgdata pgdata_backup
cp -r miniodata miniodata_backup
```

### استعادة البيانات:

```bash
# استعادة قاعدة البيانات:
docker-compose up -d postgres
docker-compose exec -T postgres psql -U postgres < backup.sql

# استعادة التخزين:
docker cp ./minio_backup blind_assist_storage:/data
```

---

## ⚠️ حل المشاكل الشائعة

### المشكلة: "Connection refused"
```bash
# الحل:
docker-compose down -v
docker-compose up --build

# انتظر 30-60 ثانية حتى تبدأ جميع الخدمات
docker-compose ps  # تحقق من الحالة
```

### المشكلة: "Port already in use"
```bash
# البورت مستخدم من قبل:
# 1. غيّر البورت في docker-compose.yml:
ports:
  - "8001:8000"  # بدلاً من 8000

# 2. أو أوقف الخدمة الأخرى:
lsof -i :8000
kill -9 <PID>
```

### المشكلة: "Out of memory"
```bash
# زيادة ذاكرة Docker:
# Windows/Mac: Docker Desktop → Settings → Resources → Memory (8GB+)
# Linux: بالفعل غير محدود

# أو قلل البيانات:
docker system prune -a --volumes
```

### المشكلة: "Cannot find image"
```bash
# الحل:
docker-compose pull
docker-compose build --no-cache

# أو إعادة كاملة:
docker-compose down -v
docker-compose up --build
```

### المشكلة: "البيانات ضاعت"
```bash
# لا تقلق، البيانات محفوظة في:
# - pgdata/    (قاعدة البيانات)
# - miniodata/ (الملفات)
# - ollama_data/ (النماذج)

# حتى مع:
docker-compose down

# البيانات تبقى! استخدم:
docker-compose down -v  # فقط إذا أردت حذف كل شيء
```

---

## 🚀 نصائح للأداء

### تحسين الأداء:

```bash
# 1. استخدم بدء في الخلفية:
docker-compose up -d

# 2. قلل السجلات:
docker-compose up --no-log-prefix

# 3. استخدم GPU إذا كان متاحاً:
# في docker-compose.yml، أضف:
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]

# 4. زيادة الذاكرة:
# Docker Desktop → Settings → Resources → Memory
```

---

## 📱 الأوامر على الهاتف (إذا كان على شبكة)

### من جهاز آخر على الشبكة:

```bash
# افتح في المتصفح (استبدل IP بـ IP الحاسوب):
http://<COMPUTER_IP>:8000/client/

# أو:
http://192.168.1.100:8000/client/
```

### للعثور على IP الحاسوب:

```bash
# Linux/Mac:
hostname -I

# Windows:
ipconfig

# Docker:
docker-compose exec fastapi hostname -I
```

---

## 🎯 الملخص السريع

| الأمر | الوظيفة |
|------|---------|
| `docker-compose up --build` | بدء كامل |
| `docker-compose down` | إيقاف |
| `docker-compose ps` | حالة الخدمات |
| `docker-compose logs -f` | عرض السجلات |
| `docker-compose exec fastapi bash` | دخول الحاوية |
| `docker-compose restart` | إعادة تشغيل |
| `docker-compose build` | إعادة بناء |

---

## 📞 الدعم السريع

```bash
# كل شيء لا يعمل؟
docker-compose down -v
docker-compose up --build

# غالباً يحل 90% من المشاكل!
```

---

**ملاحظة:** اتبع هذه الأوامر بالترتيب الموصى به للحصول على أفضل النتائج.

**الحالة:** ✅ جاهز للاستخدام الفوري
