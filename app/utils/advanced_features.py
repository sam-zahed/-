"""
PHASE 4: الميزات الجديدة المتقدمة
- كشف الأصوات البيئية
- تنبيهات ديناميكية للأشياء القريبة
- تكامل مع خدمات الخرائط
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

# محاولة استيراد librosa، لكن يعمل بدونها
try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    print("⚠️ librosa not available, using basic audio analysis")

# ============ PHASE 4.1: كشف الأصوات البيئية ============

class AmbientSoundDetector:
    """كاشف الأصوات المحيطة"""
    
    # توقيعات الأصوات (Frequencies الرئيسية)
    SOUND_SIGNATURES = {
        'car_traffic': {
            'freq_range': (500, 2000),  # Hz
            'characteristics': 'continuous_hum'
        },
        'bicycle_bell': {
            'freq_range': (1000, 3000),
            'characteristics': 'sharp_tone'
        },
        'crowd': {
            'freq_range': (200, 4000),
            'characteristics': 'variable_noise'
        },
        'rain': {
            'freq_range': (100, 500),
            'characteristics': 'white_noise'
        },
        'wind': {
            'freq_range': (50, 300),
            'characteristics': 'low_frequency_rumble'
        },
        'dog_barking': {
            'freq_range': (500, 1500),
            'characteristics': 'impulse_repetitive'
        }
    }
    
    # الأماكن المتوقعة
    EXPECTED_SOUNDS = {
        'street': ['car_traffic', 'bicycle_bell', 'crowd'],
        'park': ['bird_singing', 'wind', 'crowd'],
        'home': ['quiet_background', 'household_noise'],
        'market': ['crowd', 'wind'],
        'river': ['water_flow', 'birds']
    }
    
    def __init__(self, sample_rate: int = 22050):
        self.sample_rate = sample_rate
    
    def analyze_audio(self, audio_bytes: bytes) -> Dict[str, float]:
        """
        حلل الصوت وحدد الأصوات البيئية
        
        Return: {'sound_type': confidence, ...}
        """
        try:
            # تحويل البيانات الثنائية لـ numpy
            audio_data = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32)
            
            # تطبيع
            if audio_data.max() != 0:
                audio_data = audio_data / np.max(np.abs(audio_data))
            
            # احسب FFT
            freq_spectrum = np.abs(np.fft.fft(audio_data))
            freqs = np.fft.fftfreq(len(audio_data), 1/self.sample_rate)
            
            # تحليل الخصائص
            spectral_centroid = self._calculate_spectral_centroid(audio_data, freqs, freq_spectrum)
            zero_crossing_rate = self._calculate_zcr(audio_data)
            rms_energy = np.sqrt(np.mean(audio_data ** 2))
            
            # تصنيف الأصوات
            sound_scores = {}
            
            for sound_type, sig in self.SOUND_SIGNATURES.items():
                score = self._match_sound_signature(
                    freq_spectrum, freqs, spectral_centroid, 
                    zero_crossing_rate, rms_energy, sig
                )
                sound_scores[sound_type] = score
            
            return sound_scores
        
        except Exception as e:
            print(f"⚠️ Error analyzing audio: {e}")
            return {}
    
    def _calculate_spectral_centroid(self, audio, freqs, spectrum):
        """احسب مركز الطيف"""
        return np.sum(freqs * spectrum) / np.sum(spectrum) if np.sum(spectrum) > 0 else 0
    
    def _calculate_zcr(self, audio):
        """احسب معدل تقاطع الصفر"""
        return np.sum(np.abs(np.diff(np.sign(audio)))) / (2 * len(audio))
    
    def _match_sound_signature(self, spectrum, freqs, centroid, zcr, rms, signature):
        """طابق مع توقيع صوت معروف"""
        freq_min, freq_max = signature['freq_range']
        
        # احسب الطاقة في النطاق المتوقع
        mask = (freqs >= freq_min) & (freqs <= freq_max)
        energy_in_range = np.sum(spectrum[mask]) if np.any(mask) else 0
        total_energy = np.sum(spectrum)
        
        energy_ratio = energy_in_range / total_energy if total_energy > 0 else 0
        
        # احسب الثقة بناءً على الخصائص
        confidence = energy_ratio
        
        if signature['characteristics'] == 'continuous_hum' and zcr < 0.1:
            confidence *= 1.2
        elif signature['characteristics'] == 'sharp_tone' and zcr > 0.3:
            confidence *= 1.1
        elif signature['characteristics'] == 'white_noise' and rms > 0.1:
            confidence *= 1.1
        
        return min(confidence, 1.0)
    
    def infer_location(self, sound_scores: Dict[str, float]) -> Optional[str]:
        """استنتج الموقع من الأصوات المسموعة"""
        if not sound_scores:
            return None
        
        sorted_sounds = sorted(sound_scores.items(), key=lambda x: x[1], reverse=True)
        detected_sounds = [s[0] for s in sorted_sounds if s[1] > 0.3]
        
        for location, expected_sounds in self.EXPECTED_SOUNDS.items():
            matches = sum(1 for s in detected_sounds if s in expected_sounds)
            if matches >= 2:
                return location
        
        # الموقع الافتراضي حسب الأصوات الرئيسية
        if detected_sounds:
            if 'car_traffic' in detected_sounds or 'bicycle_bell' in detected_sounds:
                return 'street'
            elif 'crowd' in detected_sounds:
                return 'market'
            elif 'wind' in detected_sounds or 'water_flow' in detected_sounds:
                return 'park'
        
        return None

# ============ PHASE 4.2: تنبيهات ديناميكية ============

@dataclass
class DynamicAlert:
    """تنبيه ديناميكي"""
    object_class: str
    distance: float
    distance_trend: str  # 'approaching', 'stable', 'moving_away'
    urgency_level: int  # 1-5 (1 = منخفض، 5 = حرج جداً)
    recommendation: str
    timestamp: datetime

class DynamicAlertSystem:
    """نظام التنبيهات الديناميكية"""
    
    def __init__(self):
        self.object_history: Dict[str, List[Tuple[float, datetime]]] = {}
        self.tracking_window = 10  # الثواني
    
    def track_object(self, object_class: str, distance: float) -> Optional[DynamicAlert]:
        """
        تتبع كائن وحدد ما إذا كان يقترب
        """
        now = datetime.now()
        
        if object_class not in self.object_history:
            self.object_history[object_class] = []
        
        # أضف القياس الجديد
        self.object_history[object_class].append((distance, now))
        
        # احتفظ فقط بالقياسات في الفترة الزمنية
        cutoff_time = now.timestamp() - self.tracking_window
        self.object_history[object_class] = [
            (d, t) for d, t in self.object_history[object_class]
            if t.timestamp() > cutoff_time
        ]
        
        if len(self.object_history[object_class]) < 2:
            return None
        
        # احسب الاتجاه
        distances = [d for d, _ in self.object_history[object_class]]
        distance_trend = self._calculate_trend(distances)
        
        # احسب مستوى الإلحاح
        urgency = self._calculate_urgency(object_class, distance, distance_trend)
        
        # توصية الإجراء
        recommendation = self._generate_recommendation(object_class, distance, distance_trend)
        
        return DynamicAlert(
            object_class=object_class,
            distance=distance,
            distance_trend=distance_trend,
            urgency_level=urgency,
            recommendation=recommendation,
            timestamp=now
        )
    
    def _calculate_trend(self, distances: List[float]) -> str:
        """احسب اتجاه المسافة"""
        if len(distances) < 2:
            return 'stable'
        
        # معادلة الانحدار البسيطة
        x = np.arange(len(distances))
        y = np.array(distances)
        
        # حساب الميل
        slope = np.polyfit(x, y, 1)[0]
        
        if slope > -0.05:  # بطيء جداً أو ثابت
            return 'stable'
        elif slope < -0.2:  # سريع الاقتراب
            return 'approaching'
        else:
            return 'approaching'  # اقتراب عادي
    
    def _calculate_urgency(self, obj_class: str, distance: float, trend: str) -> int:
        """احسب مستوى الإلحاح (1-5)"""
        # الأساس على المسافة
        if distance < 0.5:
            base_urgency = 5
        elif distance < 1.0:
            base_urgency = 4
        elif distance < 2.0:
            base_urgency = 3
        elif distance < 5.0:
            base_urgency = 2
        else:
            base_urgency = 1
        
        # زيادة الإلحاح إذا كان يقترب
        if trend == 'approaching':
            base_urgency = min(base_urgency + 1, 5)
        
        # كائنات حرجة دائماً بأولوية عالية
        critical_objects = ['stairs', 'hole', 'car', 'person']
        if obj_class in critical_objects and base_urgency < 3:
            base_urgency = 3
        
        return base_urgency
    
    def _generate_recommendation(self, obj_class: str, distance: float, trend: str) -> str:
        """توصية الإجراء"""
        recommendations = {
            'stairs': {
                'approaching': 'احذر! درج قريب جداً. توقف فوراً',
                'stable': 'درج أمامك. كن حذراً',
                'moving_away': 'الدرج يبتعد'
            },
            'car': {
                'approaching': 'سيارة تقترب بسرعة! تحرك جانباً',
                'stable': 'سيارة بالقرب. كن منتبهاً',
                'moving_away': 'السيارة تبتعد'
            },
            'hole': {
                'approaching': 'حفرة! توقف فوراً',
                'stable': 'حفرة أمامك. تجنبها',
                'moving_away': 'الحفرة خلفك'
            },
            'person': {
                'approaching': 'شخص يقترب منك',
                'stable': 'شخص بالقرب',
                'moving_away': 'الشخص يبتعد'
            }
        }
        
        if obj_class in recommendations:
            return recommendations[obj_class].get(trend, 'كن حذراً')
        
        # توصيات عامة
        if trend == 'approaching' and distance < 1.0:
            return f'احذر! {obj_class} يقترب'
        elif distance < 0.5:
            return f'توقف! {obj_class} قريب جداً'
        else:
            return f'انتبه لـ {obj_class}'

# ============ PHASE 4.3: تكامل مع خدمات الخرائط ============

class LocationAwareness:
    """الوعي بالموقع الجغرافي"""
    
    def __init__(self):
        self.known_locations: Dict[str, Dict] = {}
        self.current_location = None
        self.journey_history = []
    
    def register_location(self, name: str, latitude: float, longitude: float, 
                         description: str = "") -> None:
        """سجل موقعاً معروفاً"""
        self.known_locations[name] = {
            'latitude': latitude,
            'longitude': longitude,
            'description': description,
            'registered_at': datetime.now().isoformat()
        }
    
    def estimate_progress_to_destination(self, current_distance: float, 
                                        total_distance: float) -> Dict:
        """
        احسب التقدم نحو الوجهة
        """
        if total_distance == 0:
            return {}
        
        progress_percent = (1 - current_distance / total_distance) * 100
        remaining_distance = current_distance
        
        # حساب الوقت المتوقع (بافتراض سرعة 1.4 م/ث)
        avg_speed = 1.4  # متر/ثانية
        estimated_time_seconds = remaining_distance / avg_speed
        estimated_time_minutes = estimated_time_seconds / 60
        
        return {
            'progress_percent': max(0, min(100, progress_percent)),
            'remaining_distance': remaining_distance,
            'estimated_time_minutes': estimated_time_minutes,
            'estimated_arrival': datetime.now().timestamp() + estimated_time_seconds
        }
    
    def suggest_next_landmark(self, remaining_landmarks: List[str]) -> Optional[str]:
        """اقترح أقرب معلم"""
        if not remaining_landmarks:
            return None
        
        # في التطبيق الحقيقي، استخدم بيانات GPS
        # الآن فقط أرجع الأول
        return remaining_landmarks[0] if remaining_landmarks else None

# إنشاء مثيلات عامة
ambient_sound_detector = AmbientSoundDetector()
dynamic_alert_system = DynamicAlertSystem()
location_awareness = LocationAwareness()
