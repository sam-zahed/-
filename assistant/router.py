"""
API للمساعد الذكي - Assistant Router
نقطة الدخول الرئيسية للمحادثة مع المستخدم

Endpoints:
- POST /chat - محادثة صوتية (صوت + صورة → رد صوتي)
- POST /analyze - تحليل صامت (صورة → تنبيهات فقط)
- POST /command - أمر نصي (نص → رد)
"""

from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict
import base64
import io
import urllib.parse

from .brain import assistant_brain, CommandType
from .context_manager import context_manager
from .alert_manager import alert_manager, AlertMode

# Import vision and audio
from app.vision.model import detector
from app.audio.transcribe import transcribe_audio_bytes
from app.audio.tts import synthesize_text
from app.spatial_awareness.stationary_detector import stationary_detector
from app.vision.ocr_reader import ocr_reader
import numpy as np
import cv2

router = APIRouter()


# ======== Models ========

class TextCommand(BaseModel):
    """أمر نصي"""
    text: str
    image_b64: Optional[str] = None


class AnalyzeRequest(BaseModel):
    """طلب تحليل صامت"""
    image_b64: str
    check_motion: Optional[bool] = True


class ModeChange(BaseModel):
    """تغيير الوضع"""
    mode: str  # 'quiet', 'normal', 'walking', 'scanning'


# ======== Helper Functions ========

def decode_image(image_b64: str) -> bytes:
    """فك تشفير صورة base64"""
    if "," in image_b64:
        _, encoded = image_b64.split(",", 1)
    else:
        encoded = image_b64
    return base64.b64decode(encoded)


def detect_objects(image_bytes: bytes) -> List[Dict]:
    """كشف الأشياء في الصورة"""
    try:
        detections = detector.detect(image_bytes, target_lang='ar')
        return detections
    except Exception as e:
        print(f"⚠️ Detection error: {e}")
        return []


def read_text_from_image(image_bytes: bytes) -> str:
    """قراءة النصوص من الصورة"""
    try:
        # استخدام دالة الغلاف التي تدعم لغات متعددة (عربي + دنماركي)
        results = ocr_reader.read_text(image_bytes)
        if not results:
            return ""
            
        texts = [res['text'] for res in results]
        return " ".join(texts)
    except Exception as e:
        print(f"⚠️ OCR error: {e}")
        return ""


# ======== Main Endpoints ========

from starlette.concurrency import run_in_threadpool

@router.post('/chat')
async def chat_with_assistant(
    audio: UploadFile = File(...),
    image: Optional[str] = Form(None)
):
    """
    محادثة صوتية كاملة
    
    يستقبل: صوت المستخدم + صورة (اختياري)
    يرجع: صوت الرد
    """
    try:
        # 1. تحويل الصوت لنص (Blocking - Run in threadpool)
        audio_bytes = await audio.read()
        user_text = await run_in_threadpool(transcribe_audio_bytes, audio_bytes)
        
        if not user_text or "[" in user_text:
            # فشل التعرف
            response_text = "لم أسمعك جيداً، أعد من فضلك"
            command = assistant_brain.parse_command("") # Dummy
        else:
            # 2. فهم الأمر
            command = assistant_brain.parse_command(user_text)
            
            # 3. تحليل الصورة إذا موجودة
            objects = []
            if image:
                image_bytes = await run_in_threadpool(decode_image, image)
                objects = await run_in_threadpool(detect_objects, image_bytes)
                context_manager.update_objects(objects)
                
                # تحليل الحركة
                motion_state = await run_in_threadpool(stationary_detector.analyze_frame, image_bytes)
                context_manager.update_user_state(is_stationary=motion_state.is_stationary)
                alert_manager.set_stationary(motion_state.is_stationary)
                
                # إذا أمر قراءة
                if command.command_type == CommandType.READ:
                    text = await run_in_threadpool(read_text_from_image, image_bytes)
                    if text:
                        response_text = f"مكتوب: {text}"
                    else:
                        response_text = "لم أجد نصاً واضحاً"
                
                # إذا أمر حفظ وجه
                elif command.command_type == CommandType.LEARN_FACE:
                    if hasattr(detector, 'face_recognizer') and detector.face_recognizer:
                        name = command.target
                        if name:
                            # face register depends on detector state, run in threadpool
                            success = await run_in_threadpool(detector.face_recognizer.register_face, name, image_bytes)
                            if success:
                                response_text = f"تم حفظ وجه {name} بنجاح"
                            else:
                                response_text = "لم أتمكن من حفظ الوجه، حاول مرة أخرى بصورة أوضح"
                        else:
                            response_text = "ما هو الاسم؟ قل 'هذا أحمد' مثلاً"
                    else:
                        response_text = "نظام التعرف على الوجوه غير مفعل"

                else:
                    # توليد الرد (May call LLM - Blocking)
                    context = context_manager.get_context_summary()
                    response_text = await run_in_threadpool(assistant_brain.generate_response, command, context, objects, image)
            else:
                context = context_manager.get_context_summary()
                response_text = await run_in_threadpool(assistant_brain.generate_response, command, context, [], None)
            
            # تنفيذ الأوامر الخاصة
            if command.command_type == CommandType.QUIET:
                alert_manager.set_mode(AlertMode.QUIET)
                context_manager.set_quiet_mode(True)
            elif command.command_type == CommandType.TALK:
                alert_manager.set_mode(AlertMode.NORMAL)
                context_manager.set_quiet_mode(False)
        
        # 4. حفظ في السياق
        context_manager.add_conversation_turn(
            user_input=user_text,
            assistant_response=response_text
        )
        
        # 5. تحويل الرد لصوت (Blocking - Run in threadpool)
        audio_response = await run_in_threadpool(synthesize_text, response_text)
        
        if audio_response:
            return StreamingResponse(
                io.BytesIO(audio_response),
                media_type="audio/wav",
                headers={
                    "X-Response-Text": urllib.parse.quote(response_text),
                    "X-Command-Type": command.command_type.value if command else "unknown"
                }
            )
        else:
            # إرجاع نص إذا فشل TTS
            return {
                "text": response_text,
                "audio": None,
                "command": command.command_type.value if command else "unknown"
            }
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"CRITICAL ERROR IN CHAT: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/command')
async def process_text_command(request: TextCommand):
    """
    معالجة أمر نصي
    """
    try:
        # فهم الأمر
        command = assistant_brain.parse_command(request.text)
        
        # تحليل الصورة إذا موجودة
        objects = []
        if request.image_b64:
            image_bytes = await run_in_threadpool(decode_image, request.image_b64)
            objects = await run_in_threadpool(detect_objects, image_bytes)
            context_manager.update_objects(objects)
            
            # إذا أمر قراءة
            if command.command_type == CommandType.READ:
                text = await run_in_threadpool(read_text_from_image, image_bytes)
                if text:
                    response_text = f"مكتوب: {text}"
                else:
                    response_text = "لم أجد نصاً واضحاً"
            else:
                context = context_manager.get_context_summary()
                response_text = await run_in_threadpool(assistant_brain.generate_response, command, context, objects, request.image_b64)
        else:
            context = context_manager.get_context_summary()
            response_text = await run_in_threadpool(assistant_brain.generate_response, command, context, context_manager.last_objects, None)
        
        # تنفيذ الأوامر الخاصة
        if command.command_type == CommandType.QUIET:
            alert_manager.set_mode(AlertMode.QUIET)
            context_manager.set_quiet_mode(True)
        elif command.command_type == CommandType.TALK:
            alert_manager.set_mode(AlertMode.NORMAL)
            context_manager.set_quiet_mode(False)
        
        # حفظ في السياق
        context_manager.add_conversation_turn(
            user_input=request.text,
            assistant_response=response_text,
            action=command.command_type.value
        )
        
        return {
            "text": response_text,
            "command_type": command.command_type.value,
            "objects_count": len(objects)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/analyze')
def analyze_scene_silently(request: AnalyzeRequest):
    """
    تحليل صامت - فقط تنبيهات مهمة
    RUNS AS SYNC DEF to prevent blocking event loop
    """
    try:
        image_bytes = decode_image(request.image_b64)
        
        # تحليل الحركة
        if request.check_motion:
            motion_state = stationary_detector.analyze_frame(image_bytes)
            alert_manager.set_stationary(motion_state.is_stationary)
            context_manager.update_user_state(is_stationary=motion_state.is_stationary)
        
        # كشف الأشياء
        objects = detect_objects(image_bytes)
        context_manager.update_objects(objects)
        
        # فلترة التنبيهات الذكية
        filtered = alert_manager.filter_objects(objects)
        
        # توليد رسالة صوتية واحدة (إذا يوجد تنبيهات)
        speak_message = alert_manager.get_speak_message(filtered)
        
        return {
            "objects_count": len(objects),
            "alerts_count": len(filtered),
            "alerts": filtered,
            "speak_message": speak_message,
            "should_speak": len(speak_message) > 0,
            "is_stationary": alert_manager.is_stationary,
            "mode": alert_manager.current_mode.value
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/mode')
async def change_mode(request: ModeChange):
    """تغيير وضع التنبيهات"""
    mode_map = {
        'quiet': AlertMode.QUIET,
        'normal': AlertMode.NORMAL,
        'walking': AlertMode.WALKING,
        'scanning': AlertMode.SCANNING
    }
    
    if request.mode not in mode_map:
        raise HTTPException(status_code=400, detail="Invalid mode")
    
    result = alert_manager.set_mode(mode_map[request.mode])
    
    if request.mode == 'quiet':
        context_manager.set_quiet_mode(True)
    else:
        context_manager.set_quiet_mode(False)
    
    return result


@router.get('/status')
async def get_assistant_status():
    """حالة المساعد"""
    return {
        **alert_manager.get_status(),
        **context_manager.get_context_summary()
    }


@router.post('/reset')
async def reset_assistant():
    """إعادة تعيين المساعد"""
    alert_manager.reset_cooldowns()
    alert_manager.set_mode(AlertMode.NORMAL)
    context_manager.clear_context()
    
    return {
        "message": "تم إعادة تعيين المساعد",
        "success": True
    }


@router.get('/history')
async def get_conversation_history(n: int = 5):
    """تاريخ المحادثة"""
    return {
        "history": context_manager.get_last_conversation(n)
    }
