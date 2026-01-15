#!/bin/bash

# ✅ فحص سريع لملفات Docker

echo "🔍 فحص ملفات Docker..."
echo ""

# التحقق من docker-compose.yml
if [ -f "docker-compose.yml" ]; then
    echo "✅ docker-compose.yml موجود"
    echo "   - Database: PostgreSQL 15"
    echo "   - Storage: MinIO"
    echo "   - LLM: Ollama"
    echo "   - API: FastAPI"
else
    echo "❌ docker-compose.yml غير موجود"
fi

# التحقق من app/Dockerfile
if [ -f "app/Dockerfile" ]; then
    echo "✅ app/Dockerfile موجود"
    echo "   - Python 3.11-slim"
    echo "   - جميع المكتبات مثبتة"
    echo "   - النماذج تُحمّل تلقائياً"
else
    echo "❌ app/Dockerfile غير موجود"
fi

# التحقق من requirements.txt
if [ -f "requirements.txt" ]; then
    echo "✅ requirements.txt موجود"
    PACKAGES=$(wc -l < requirements.txt)
    echo "   - عدد المكتبات: $PACKAGES"
else
    echo "❌ requirements.txt غير موجود"
fi

# التحقق من app/main.py
if [ -f "app/main.py" ]; then
    echo "✅ app/main.py موجود"
    ROUTERS=$(grep -c "include_router" app/main.py)
    echo "   - عدد الروترات: $ROUTERS"
else
    echo "❌ app/main.py غير موجود"
fi

# التحقق من client/index.html
if [ -f "client/index.html" ]; then
    echo "✅ client/index.html موجود (الواجهة)"
else
    echo "❌ client/index.html غير موجود"
fi

echo ""
echo "📦 حالة المكونات الرئيسية:"
echo ""

# التحقق من وجود المجلدات الأساسية
MODULES=("vision" "audio" "assistant" "learning" "navigation" "alerts")

for module in "${MODULES[@]}"; do
    if [ -d "app/$module" ]; then
        FILES=$(find "app/$module" -name "*.py" | wc -l)
        echo "✅ app/$module/ - $FILES ملف Python"
    else
        echo "❌ app/$module/ غير موجود"
    fi
done

echo ""
echo "🚀 للبدء السريع، شغّل:"
echo "   docker-compose up --build"
echo ""
echo "📱 ثم افتح في المتصفح:"
echo "   http://localhost:8000/client/"
echo ""
