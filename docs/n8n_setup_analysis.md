# تحليل وتوافق n8n مع المشروع

## الملخص التنفيذي
تم تحديث المشروع ليصبح متوافقاً تماماً مع ملفات `n8n Workflows`. تم إضافة خدمة `n8n` إلى Docker، وتمت برمجة جميع الـ APIs المفقودة في `FastAPI` (المجلد `app`).

**الحالة:** :white_check_mark: متوافق وجاهز للتشغيل.

---

## 1. التعديلات التي تمت

### أ. البنية التحتية (Infrastructure)
- **Docker Compose:** تم إضافة خدمة `n8n` (بورت 5678) وحجم بيانات `n8n_data`.
- **Database:** تم تفعيل `SQLAlchemy` وإنشاء جداول قاعدة البيانات:
    - `events`: لتخزين الأحداث من الـ Workflow الأول.
    - `change_queue`: لقائمة التغييرات (Workflow الثاني).
    - `map_features`: لتخزين معالم الخريطة المؤكدة.
    - `labeling_tasks`: لمهام التوسيم (Workflow الثالث).

### ب. الـ API Endpoints الجديدة
تم إضافة الـ Routers التالية لتلبيه طلبات n8n:

| n8n Node Requirement | New FastAPI Endpoint | Description |
| :--- | :--- | :--- |
| **Realtime Model** | `POST /infer/realtime` | يستقبل الصور (Base64) ويرجع الكائنات وتقدير المسافة (Mock/Real). |
| **Store Event** | `POST /events/create` | يخزن تفاصيل الحدث والقرار في قاعدة البيانات. |
| **Change Queue** | `POST /change_queue/batch_add` | يضيف مخرجات الاستشعار لقائمة التغييرات المعلقة. |
| **Pending Changes** | `GET /change_queue/pending` | يجلب التغييرات لـ n8n لمعالجتها دورياً. |
| **Reject Change** | `POST /change_queue/reject` | يرفض التغيير من قبل n8n. |
| **Base Map** | `POST /base_map/add_feature` | يضيف معلم جديد للخريطة بعد التأكد منه. |
| **Notifications** | `POST /notifications/send` | (Mock) يرسل إشعارات للمستخدمين. |
| **Labeling** | `GET /labeling_queue/top_k` | يجلب الصور غير المؤكدة للتعلم النشط. |

---

## 2. كيفية التشغيل (How to Run)

### الخطوة 1: بناء وتشغيل الحاويات
من مجلد المشروع الرئيسي:

```bash
docker compose up -d --build
```
*سيقوم هذا الأمر ببناء الـ Image الجديدة لـ FastAPI وتشغيل n8n و Postgres و MinIO.*

### الخطوة 2: إعداد n8n
1.  افتح المتصفح: `http://localhost:5678`
2.  سجل الدخول:
    - **User:** admin
    - **Pass:** password
3.  **Import Workflows:**
    - اذهب إلى القائمة الجانبية -> **Workflows** -> **Import**.
    - اختر ملفات JSON من المجلد `n8n_templates`.
4.  **Activate:** قم بتفعيل الـ Workflows (Switch Active).

### الخطوة 3: الاختبار
يمكنك اختبار الـ Endpoints يدوياً عبر Swagger UI:
`http://localhost:8000/docs`

ستجد أقسام جديدة: `infer`, `events`, `change_queue`, etc.

---
**ملاحظة:** الروابط داخل n8n Nodes تشير إلى `http://fastapi:8000`. هذا صحيح ولا يحتاج تعديل لأن n8n يعمل داخل شبكة Docker ويتصل بـ FastAPI عبر اسم الخدمة.
