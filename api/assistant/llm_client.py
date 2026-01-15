import requests
import json
import time

class LLMClient:
    def __init__(self, host="http://ollama:11434", model="llama3.2:1b", vision_model="moondream"):
        self.host = host
        self.model = model
        self.vision_model = vision_model
        self.is_ready = False

    def check_connection(self) -> bool:
        """التحقق من اتصال Ollama"""
        try:
            print(f"⏳ Connecting to AI Brain ({self.host})...")
            response = requests.get(f"{self.host}/")
            if response.status_code == 200:
                print("✅ AI Brain Connected")
                self.is_ready = True
                return True
        except Exception:
            print("❌ AI Brain not reachable (Ollama down?)")
        return False

    def ensure_model(self):
        """التأكد من وجود الموديلات (Text + Vision)"""
        if not self.check_connection():
            return False
            
        try:
            # Check installed models
            response = requests.get(f"{self.host}/api/tags")
            models = [m['name'] for m in response.json()['models']]
            
            # Check Text Model
            if self.model not in models and f"{self.model}:latest" not in models:
                print(f"📥 Pulling text model {self.model}...")
                requests.post(f"{self.host}/api/pull", json={"name": self.model})
            
            # Check Vision Model
            if self.vision_model not in models and f"{self.vision_model}:latest" not in models:
                print(f"📥 Pulling vision model {self.vision_model}...")
                requests.post(f"{self.host}/api/pull", json={"name": self.vision_model})
                
            print(f"✅ Models ({self.model}, {self.vision_model}) check initiated")
            return True
        except Exception as e:
            print(f"⚠️ Model check failed: {e}")
            return False

    def chat(self, prompt: str, system_prompt: str = None, image_b64: str = None) -> str:
        """محادثة ذكية (نص أو صور)"""
        if not self.is_ready:
            if not self.check_connection():
                return "عذراً، عقلي الذكي غير متصل حالياً."

        url = f"{self.host}/api/generate"
        
        # Determine model
        target_model = self.vision_model if image_b64 else self.model
        
        full_prompt = prompt
        # Note: LLaVA and Llama sometimes behave differently with system prompts.
        # usually simpler is better for VLM.
        if system_prompt and not image_b64:
             full_prompt = f"System: {system_prompt}\nUser: {prompt}"

        payload = {
            "model": target_model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": 0.7
            }
        }
        
        if image_b64:
            # Clean base64 if needed
            if "," in image_b64:
                image_b64 = image_b64.split(",", 1)[1]
            payload["images"] = [image_b64]
        
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                return response.json()['response']
            else:
                return f"Error: {response.text}"
        except Exception as e:
            return f"Thinking Error: {e}"
