"""
PHASE 2: نظام التخزين المؤقت (Caching System)
تسريع المعالجة بحفظ النتائج المتطابقة
"""

import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path
import time

class CacheManager:
    """مدير التخزين المؤقت"""
    
    def __init__(self, ttl: int = 30, cache_dir: Optional[Path] = None):
        """
        ttl: عمر الكاش (بالثواني)
        cache_dir: مجلد التخزين (None = الذاكرة فقط)
        """
        self.ttl = ttl
        self.cache_dir = cache_dir or Path('/tmp/vision_cache')
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        
        if cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _hash_image(self, image_bytes: bytes) -> str:
        """حساب بصمة الصورة"""
        return hashlib.md5(image_bytes).hexdigest()
    
    def get(self, image_bytes: bytes, prefix: str = 'img') -> Optional[Dict]:
        """استرجع من الكاش"""
        image_hash = self._hash_image(image_bytes)
        cache_key = f"{prefix}_{image_hash}"
        
        # تحقق من الذاكرة أولاً
        if cache_key in self.memory_cache:
            entry = self.memory_cache[cache_key]
            if datetime.now() < entry['expires_at']:
                return entry['data']
            else:
                # انتهت مدة الكاش
                del self.memory_cache[cache_key]
        
        # جرب ملف الكاش إذا كان موجوداً
        if self.cache_dir:
            cache_file = self.cache_dir / f"{cache_key}.json"
            if cache_file.exists():
                try:
                    with open(cache_file, 'r') as f:
                        entry = json.load(f)
                        if datetime.fromisoformat(entry['expires_at']) > datetime.now():
                            return entry['data']
                        else:
                            cache_file.unlink()  # احذف الملف المنتهي
                except:
                    pass
        
        return None
    
    def set(self, image_bytes: bytes, data: Dict, prefix: str = 'img') -> None:
        """احفظ في الكاش"""
        image_hash = self._hash_image(image_bytes)
        cache_key = f"{prefix}_{image_hash}"
        
        entry = {
            'data': data,
            'expires_at': (datetime.now() + timedelta(seconds=self.ttl)).isoformat(),
            'created_at': datetime.now().isoformat()
        }
        
        # احفظ في الذاكرة
        self.memory_cache[cache_key] = {
            'data': data,
            'expires_at': datetime.now() + timedelta(seconds=self.ttl)
        }
        
        # احفظ في ملف
        if self.cache_dir:
            cache_file = self.cache_dir / f"{cache_key}.json"
            try:
                with open(cache_file, 'w') as f:
                    json.dump(entry, f)
            except:
                pass
    
    def clear_expired(self) -> int:
        """امسح الكاش المنتهي"""
        now = datetime.now()
        
        # من الذاكرة
        expired_keys = [
            k for k, v in self.memory_cache.items()
            if v['expires_at'] < now
        ]
        for k in expired_keys:
            del self.memory_cache[k]
        
        # من الملفات
        deleted_count = 0
        if self.cache_dir:
            for cache_file in self.cache_dir.glob('*.json'):
                try:
                    with open(cache_file, 'r') as f:
                        entry = json.load(f)
                        if datetime.fromisoformat(entry['expires_at']) < now:
                            cache_file.unlink()
                            deleted_count += 1
                except:
                    pass
        
        return len(expired_keys) + deleted_count

# إنشاء مدير كاش عام
cache_manager = CacheManager(ttl=30)

# Decorator للكاش
def cached(prefix: str = 'func', ttl: int = 30):
    """ديكوريتر لتخزين مؤقت للدوال"""
    def decorator(func):
        cache = CacheManager(ttl=ttl)
        
        async def async_wrapper(*args, **kwargs):
            # حاول من الكاش
            if args and isinstance(args[0], bytes):
                cached_result = cache.get(args[0], prefix=prefix)
                if cached_result is not None:
                    return cached_result
            
            # استدعِ الدالة الأصلية
            result = await func(*args, **kwargs) if hasattr(func, '__await__') else func(*args, **kwargs)
            
            # احفظ في الكاش
            if args and isinstance(args[0], bytes):
                cache.set(args[0], result, prefix=prefix)
            
            return result
        
        def sync_wrapper(*args, **kwargs):
            # حاول من الكاش
            if args and isinstance(args[0], bytes):
                cached_result = cache.get(args[0], prefix=prefix)
                if cached_result is not None:
                    return cached_result
            
            # استدعِ الدالة الأصلية
            result = func(*args, **kwargs)
            
            # احفظ في الكاش
            if args and isinstance(args[0], bytes):
                cache.set(args[0], result, prefix=prefix)
            
            return result
        
        # تحديد الدالة الصحيحة
        import asyncio
        import inspect
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

class PerformanceMonitor:
    """مراقب الأداء"""
    
    def __init__(self):
        self.metrics: Dict[str, list] = {}
    
    def record(self, operation: str, duration: float) -> None:
        """سجل مقياس أداء"""
        if operation not in self.metrics:
            self.metrics[operation] = []
        
        self.metrics[operation].append({
            'timestamp': datetime.now().isoformat(),
            'duration': duration
        })
        
        # احتفظ بآخر 100 قياس فقط
        if len(self.metrics[operation]) > 100:
            self.metrics[operation] = self.metrics[operation][-100:]
    
    def get_average(self, operation: str) -> float:
        """احصل على متوسط المدة"""
        if operation not in self.metrics or not self.metrics[operation]:
            return 0.0
        
        durations = [m['duration'] for m in self.metrics[operation]]
        return sum(durations) / len(durations)
    
    def get_stats(self) -> Dict[str, Dict]:
        """احصل على إحصائيات مفصلة"""
        stats = {}
        for op, metrics in self.metrics.items():
            if metrics:
                durations = [m['duration'] for m in metrics]
                stats[op] = {
                    'count': len(durations),
                    'avg': sum(durations) / len(durations),
                    'min': min(durations),
                    'max': max(durations),
                    'last': durations[-1]
                }
        return stats

# إنشاء مراقب أداء عام
perf_monitor = PerformanceMonitor()

def timed(operation: str):
    """ديكوريتر لقياس الوقت"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            result = await func(*args, **kwargs)
            duration = time.time() - start
            perf_monitor.record(operation, duration)
            return result
        
        def sync_wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start
            perf_monitor.record(operation, duration)
            return result
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
