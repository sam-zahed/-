"""
قراءة النصوص من الصور باستخدام EasyOCR
يدعم العربية والإنجليزية
"""

import cv2
import numpy as np
from typing import List, Dict

class OCRReader:
    def __init__(self):
        self.reader = None
        self.load_model()
    
    def load_model(self):
        """تحميل نموذج EasyOCR"""
        self.readers = []
        try:
            import easyocr
            
            # قارئ 1: العربية والإنجليزية
            print("⏳ Loading OCR Reader 1 (Arabic + English)...")
            self.readers.append(easyocr.Reader(['ar', 'en'], gpu=False))
            
            # قارئ 2: الدنماركية والإنجليزية
            print("⏳ Loading OCR Reader 2 (Danish + English)...")
            self.readers.append(easyocr.Reader(['da', 'en'], gpu=False))
            
            print("✅ OCR Readers loaded successfully")
            
        except ImportError:
            print("⚠️ EasyOCR not installed. Install with: pip install easyocr")
            print("   OCR features will not be available")
        except Exception as e:
            print(f"⚠️ OCR Reader error: {e}")
    
    def _preprocess_image(self, img):
        """معالجة الصورة لتحسين القراءة"""
        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            return enhanced
        except:
            return img

    def read_text(self, image_bytes) -> List[Dict]:
        """قراءة النصوص من صورة باستخدام كل القارئات"""
        if not self.readers:
            return []
        
        try:
            arr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            
            if img is None:
                return []
            
            # قائمة لتجميع النتائج الفريدة
            combined_results = []
            seen_texts = set()

            # دالة مساعدة لتشغيل القراءة
            def run_ocr(reader, image, lang_group):
                results = reader.readtext(image)
                for (bbox, text, confidence) in results:
                    if confidence > 0.3 and text not in seen_texts:
                        seen_texts.add(text)
                        combined_results.append({
                            'text': text,
                            'confidence': round(confidence, 2),
                            'bbox': bbox,
                            'language': 'ar' if self._is_arabic(text) else lang_group
                        })

            # المحاولة 1: الصورة الأصلية
            for i, reader in enumerate(self.readers):
                lang_group = 'ar' if i == 0 else 'da' # تقريب بسيط، سيتم فحصه بالدالة _is_arabic
                run_ocr(reader, img, lang_group)

            # المحاولة 2: تحسين التباين (إذا النتائج قليلة)
            if len(combined_results) == 0:
                processed_img = self._preprocess_image(img)
                for i, reader in enumerate(self.readers):
                    lang_group = 'ar' if i == 0 else 'da'
                    run_ocr(reader, processed_img, lang_group)
            
            return combined_results
            
        except Exception as e:
            print(f"⚠️ OCR error: {e}")
            return []
    
    def _is_arabic(self, text: str) -> bool:
        """كشف إذا كان النص عربي"""
        if not text:
            return False
        
        arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
        return arabic_chars > len(text) / 2
    
    def get_combined_text(self, texts: List[Dict]) -> str:
        """دمج جميع النصوص المكتشفة"""
        if not texts:
            return ""
        
        return ' . '.join([t['text'] for t in texts])

# إنشاء instance عام
ocr_reader = OCRReader()
