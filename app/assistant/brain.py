"""
دماغ المساعد الذكي - Assistant Brain
يفهم الأوامر ويقرر الرد المناسب

الأوامر المدعومة:
- "ماذا أمامي؟" → وصف المشهد
- "أين أنا؟" → استنتاج المكان
- "أين الباب؟" → البحث عن شيء
- "اقرأ" → قراءة النصوص
- "اسكت" → وضع الصمت
- "دور حولي" → مسح 360°
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import re
from collections import Counter
from .llm_client import LLMClient

class CommandType(Enum):
    DESCRIBE = "describe"      # وصف المشهد
    FIND = "find"              # البحث عن شيء
    READ = "read"              # قراءة نصوص
    SCAN = "scan"              # بحث مستمر
    QUIET = "quiet"            # وضع الصامت
    TALK = "talk"              # وضع التحدث
    HELP = "help"              # مساعدة
    EXPAND = "expand"          # توسيع الوعي
    STATUS = "status"          # حالة النظام
    WHERE = "where"            # أين أنا
    LEARN_FACE = "learn_face"  # حفظ وجه
    CHAT = "chat"              # محادثة عامة (LLM)
    UNKNOWN = "unknown"        # غير معروف


@dataclass
class ParsedCommand:
    """أمر محلل"""
    command_type: CommandType
    target: Optional[str] = None      # الهدف (مثل: "باب")
    direction: Optional[str] = None   # الاتجاه (مثل: "يمين")
    original_text: str = ""
    confidence: float = 1.0


class AssistantBrain:
    """
    دماغ المساعد - يفهم الأوامر ويولّد الردود
    """
    
    def __init__(self):
        # تهيئة عميل الذكاء الاصطناعي
        self.llm_client = LLMClient()
        
        # خرائط الغرف (استنتاج)
        self.room_map = {
            'المطبخ': ['refrigerator', 'fridge', 'sink', 'stove', 'oven', 'microwave', 'cabinet', 'dining table', 'bottle', 'cup', 'glass'],
            'غرفة النوم': ['bed', 'wardrobe', 'closet', 'lamp', 'pillow', 'blanket'],
            'الصالة': ['sofa', 'couch', 'tv', 'monitor', 'screen', 'coffee table', 'armchair'],
            'الحمام': ['toilet', 'sink', 'mirror', 'towel', 'shower', 'bathtub'],
            'المكتب': ['desk', 'computer', 'laptop', 'bookcase', 'shelf', 'printer', 'books'],
            'الشارع': ['car', 'truck', 'bus', 'tree', 'traffic light', 'stop sign', 'bicycle', 'motorcycle'],
        }

        # أنماط الأوامر
        # أنماط الأوامر (لهجات متنوعة)
        self.command_patterns = {
            CommandType.DESCRIBE: [
                # MSA
                r'ماذا أما[مى]', r'ماذا ترى', r'صف',
                # Egyptian
                r'ايه ده', r'فيه ايه', r'بص', r'شايف ايه',
                # Gulf / Levantine
                r'ايش قدامي', r'شو في', r'ايش تشوف', r'شنو هذا', r'وش ذا',
                # English
                r'what.*front', r'describe',
            ],
            CommandType.WHERE: [
                # MSA
                r'أين أنا', r'في أي غرفة', r'مكاني',
                # Dialects
                r'وين أنا', r'فين أنا', r'انا فين', r'ويني',
                # English
                r'where am i',
            ],
            CommandType.LEARN_FACE: [
                r'هذا (.+)', r'هذه (.+)', r'تعرف على (.+)',
                # Egyptian
                r'ده (.+)', r'دي (.+)', r'سجل وش (.+)',
                # Gulf / Levantine
                r'عرف (.+)', r'احفظ شكل (.+)',
                # English
                r'this is (.+)', 
            ],
            CommandType.FIND: [
                # MSA
                r'أين\s+(.+)', r'ابحث عن\s+(.+)', r'هل يوجد\s+(.+)',
                # Egyptian
                r'فين\s+(.+)', r'هو فيه\s+(.+)',
                # Gulf / Levantine
                r'وين\s+(.+)', r'دور علي\s+(.+)',
                # English
                r'where.*is\s+(.+)', r'find\s+(.+)',
            ],
            CommandType.READ: [
                r'اقرأ', r'ماذا مكتوب',
                # Dialects
                r'اقرا', r'ايه مكتوب', r'وش مكتوب', r'شو مكتوب',
                # English
                r'read',
            ],
            CommandType.SCAN: [
                r'دور حولي', r'مسح', r'كل شيء حولي',
                # Dialects
                r'لف', r'شوف حولين', r'ايش حولي',
                # English
                r'scan',
            ],
            CommandType.QUIET: [
                r'اسكت', r'صمت', r'توقف',
                # Dialects
                r'بس', r'هس', r'ولا كلمة', r'كفاية', r'اسه',
                # English
                r'quiet', r'stop',
            ],
            CommandType.TALK: [
                r'تكلم', r'نبهني',
                # Dialects
                r'ارجع اتكلم', r'شغّل',
                # English
                r'talk',
            ],
            CommandType.HELP: [
                r'ساعدني', r'مساعدة', r'ماذا تستطيع',
                # Dialects
                r'بتعمل ايه', r'ايش تسوي',
                # English
                r'help',
            ],
            CommandType.EXPAND: [
                r'كل شيء', r'توسيع',
                # Dialects
                r'كله', r'كل حاجة',
                # English
                r'all', r'expand',
            ],
            CommandType.STATUS: [
                r'حالة', r'كيف الوضع',
                # English
                r'status',
            ],
        }
        
        # كلمات الاتجاهات
        self.direction_words = {
            'أمام': 'front', 'امام': 'front', 'قدام': 'front', 'front': 'front',
            'يمين': 'right', 'يميني': 'right', 'right': 'right',
            'يسار': 'left', 'شمال': 'left', 'يساري': 'left', 'left': 'left',
            'خلف': 'back', 'ورا': 'back', 'back': 'back',
        }
        
        # الأشياء المعروفة (للبحث)
        self.known_objects = {
            'باب': 'door', 'door': 'door',
            'كرسي': 'chair', 'chair': 'chair',
            'طاولة': 'table', 'table': 'table',
            'شخص': 'person', 'person': 'person', 'ناس': 'person',
            'درج': 'stairs', 'stairs': 'stairs', 'سلم': 'stairs',
            'نافذة': 'window', 'window': 'window', 'شباك': 'window',
            'سيارة': 'car', 'car': 'car',
            'ثلاجة': 'refrigerator', 'fridge': 'refrigerator',
        }
    
    def parse_command(self, text: str) -> ParsedCommand:
        """تحليل النص وفهم الأمر"""
        if not text:
            return ParsedCommand(
                command_type=CommandType.UNKNOWN,
                original_text=""
            )
        
        text_lower = text.lower().strip()
        
        # محاولة مطابقة كل نوع أمر
        for cmd_type, patterns in self.command_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text_lower)
                if match:
                    target = None
                    if match.groups():
                        target = match.group(1).strip()
                        target = self._normalize_target(target)
                    direction = self._extract_direction(text_lower)
                    
                    return ParsedCommand(
                        command_type=cmd_type,
                        target=target,
                        direction=direction,
                        original_text=text,
                        confidence=1.0
                    )
        
        # إذا لم نجد أمراً محدداً، نعتبره محادثة عامة (LLM)
        if len(text) > 2:
            return ParsedCommand(
                command_type=CommandType.CHAT,
                target=text,
                original_text=text,
                confidence=0.8
            )
            
        return self._guess_command(text)
    
    def _normalize_target(self, target: str) -> str:
        """تطبيع اسم الهدف"""
        target = target.strip()
        for prefix in ['ال', 'a ', 'an ', 'the ']:
            if target.startswith(prefix):
                target = target[len(prefix):]
        if target in self.known_objects:
            return self.known_objects[target]
        return target
    
    def _extract_direction(self, text: str) -> Optional[str]:
        """استخراج الاتجاه من النص"""
        for word, direction in self.direction_words.items():
            if word in text:
                return direction
        return None
    
    def _guess_command(self, text: str) -> ParsedCommand:
        """محاولة تخمين الأمر"""
        if '?' in text or len(text.split()) <= 3:
            return ParsedCommand(
                command_type=CommandType.DESCRIBE,
                original_text=text,
                confidence=0.5
            )
        return ParsedCommand(
            command_type=CommandType.UNKNOWN,
            original_text=text,
            confidence=0.0
        )
    
    def infer_room(self, objects: List[Dict]) -> str:
        """استنتاج الغرفة بناءً على الأشياء"""
        if not objects:
            return "غير معروف"
        
        scores = {room: 0 for room in self.room_map}
        detected_classes = [obj.get('class', '').lower() for obj in objects]
        
        for room, items in self.room_map.items():
            for item in items:
                if item in detected_classes:
                    scores[room] += 1
        
        # إيجاد الغرفة الأكثر تطابقاً
        best_room = max(scores, key=scores.get)
        if scores[best_room] > 0:
            return best_room
        return "مكان غير محدد"

    def generate_response(self, 
                         command: ParsedCommand, 
                         context: Dict,
                         objects: List[Dict] = None,
                         image_b64: str = None) -> str:
        """توليد الرد المناسب للأمر"""
        objects = objects or []
        
        if command.command_type == CommandType.CHAT:
            if image_b64:
                 system_prompt = (
                    "أنت مساعد بصري ذكي. "
                    "أجب على سؤال المستخدم بناءً على الصورة التي أمامك. "
                    "كن دقيقاً ومختصراً."
                )
            else:
                system_prompt = (
                    "أنت مساعد مفيد لشخص كفيف. "
                    "تحدث بلهجة ودودة ومختصرة. "
                    f"معلومات السياق الحالي: {context.get('summary', 'لا يوجد')}. "
                    f"الأشياء التي أمامك الآن: {[obj.get('class_ar', obj.get('class')) for obj in objects]}."
                )
            # نحاول الاتصال بالموديل
            response = self.llm_client.chat(command.target, system_prompt, image_b64=image_b64)
            return response

        if command.command_type == CommandType.DESCRIBE:
            return self._generate_describe_response(objects, command.direction)
        
        elif command.command_type == CommandType.WHERE:
            room = self.infer_room(objects)
            return f"يبدو أنك في {room}"

        elif command.command_type == CommandType.FIND:
            return self._generate_find_response(command.target, objects)
        
        elif command.command_type == CommandType.READ:
            return "سأقرأ النصوص الآن..."
        
        elif command.command_type == CommandType.SCAN:
            return "ابدأ الدوران ببطء وسأخبرك بكل شيء حولك"
        
        elif command.command_type == CommandType.QUIET:
            return "حاضر، سأصمت. سأنبهك فقط على الأخطار"
        
        elif command.command_type == CommandType.TALK:
            return "تم تفعيل التنبيهات"
        
        elif command.command_type == CommandType.HELP:
            return self._generate_help_response()
        
        elif command.command_type == CommandType.EXPAND:
            return self._generate_expand_response(objects)
        
        elif command.command_type == CommandType.STATUS:
            return self._generate_status_response(context)
        
        else:
            return "لم أفهم. قل 'مساعدة' لمعرفة الأوامر"
    
    def _generate_describe_response(self, 
                                    objects: List[Dict], 
                                    direction: Optional[str] = None) -> str:
        """توليد وصف المشهد مع السياق"""
        if not objects:
            return "لا أرى شيئاً واضحاً أمامي"
        
        # استنتاج الغرفة
        room = self.infer_room(objects)
        room_intro = ""
        if room != "مكان غير محدد":
            room_intro = f"أنت في {room}. "
            
        # فلترة حسب الاتجاه إذا محدد
        if direction:
            objects = [obj for obj in objects 
                      if obj.get('direction', 'front') == direction]
            if not objects:
                return f"لا يوجد شيء على {self._direction_to_arabic(direction)}"
        
        # ترتيب حسب المسافة
        objects = sorted(objects, key=lambda x: x.get('distance_m', 999))
        
        # أهم 3 أشياء
        top_objects = objects[:3]
        
        if len(top_objects) == 1:
            obj = top_objects[0]
            name = obj.get('class_ar', obj.get('class', 'شيء'))
            dist = obj.get('distance_m', 0)
            desc = ""
            if dist < 1:
                desc = f"{name} قريب منك"
            elif dist < 2:
                desc = f"{name} على بعد متر"
            else:
                desc = f"{name} على بعد {int(dist)} متر"
            return room_intro + desc
        
        else:
            descriptions = []
            for obj in top_objects:
                name = obj.get('class_ar', obj.get('class', 'شيء'))
                descriptions.append(name)
            
            return f"{room_intro}أمامك {' و'.join(descriptions)}"
    
    def _generate_find_response(self, target: str, objects: List[Dict]) -> str:
        """توليد رد البحث"""
        if not target:
            return "ماذا تريد أن أبحث عنه؟"
        
        target_lower = target.lower()
        target_en = self.known_objects.get(target_lower, target_lower)
        
        found = []
        for obj in objects:
            obj_class = obj.get('class', '').lower()
            if target_en in obj_class or target_lower in obj.get('class_ar', '').lower():
                found.append(obj)
        
        if not found:
            return f"لم أجد {target}"
        
        closest = min(found, key=lambda x: x.get('distance_m', 999))
        name = closest.get('class_ar', target)
        dist = closest.get('distance_m', 0)
        direction = closest.get('direction_ar', 'أمامك')
        
        if dist < 1:
            return f"{name} قريب جداً {direction}"
        elif dist < 2:
            return f"{name} {direction} على بعد متر"
        else:
            return f"{name} {direction} على بعد {int(dist)} متر"
    
    def _generate_help_response(self) -> str:
        """توليد رد المساعدة"""
        return (
            "يمكنني مساعدتك في معرفة مكانك، وصف المشهد، أو قراءة النصوص"
        )
    
    def _generate_expand_response(self, objects: List[Dict]) -> str:
        """توليد رد التوسيع"""
        if not objects:
            return "المحيط خالي"
        
        count = len(objects)
        if count <= 3:
            names = [obj.get('class_ar', obj.get('class', 'شيء')) 
                    for obj in objects]
            return f"حولك {', '.join(names)}"
        else:
            return f"يوجد {count} أشياء حولك"
    
    def _generate_status_response(self, context: Dict) -> str:
        """توليد رد الحالة"""
        quiet = context.get('quiet_mode', False)
        objects_count = context.get('objects_count', 0)
        status = "وضع الصمت نشط" if quiet else "التنبيهات تعمل"
        return f"{status}. أرى {objects_count} أشياء"
    
    def _direction_to_arabic(self, direction: str) -> str:
        """تحويل الاتجاه للعربية"""
        mapping = {
            'front': 'أمامك',
            'right': 'يمينك', 
            'left': 'يسارك',
            'back': 'خلفك'
        }
        return mapping.get(direction, direction)


# Instance عام
assistant_brain = AssistantBrain()
