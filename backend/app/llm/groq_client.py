"""
============================================================
GROQ CLIENT: Cloud LLM — Zyada Smart, Zyada Fast! ☁️⚡
============================================================

📖 EXPLANATION:

Ollama = Local LLM (tumhare laptop pe chalta hai)
Groq   = Cloud LLM (Groq ke servers pe chalta hai)

Fark kya hai?
─────────────
Ollama:  Tumhare laptop pe = SLOW (phi3:mini 15-20 sec)
         But OFFLINE kaam karta hai (no internet needed)

Groq:    Groq ke powerful servers pe = FAST (2-5 sec!)
         But ONLINE chahiye (internet required)
         FREE hai (30 requests per minute free tier)

Groq ke servers pe LPU (Language Processing Unit) hai —
custom hardware jo LLM ke liye bana hai. Isliye itna fast hai!

INHERITANCE kya hai?
────────────────────
GroqClient apne papa (OllamaClient) se prompt building
methods INHERIT karta hai — matlab copy nahi karna pada!

Socho:
- Papa (OllamaClient) ke paas: prompt banane ka talent
- Beta (GroqClient) ko woh talent mila (inheritance)
- Beta ne apna naya talent add kiya: Groq API se baat karna

Code mein:
  class GroqClient(OllamaClient):  ← "OllamaClient ka beta"
    - build_voice_conversation_prompt() → papa se mila (free!)
    - build_voice_retry_prompt()       → papa se mila (free!)
    - generate_voice_response()        → APNA naya method (override)

OVERRIDE kya hai?
─────────────────
Jab beta apne papa ka kaam APNE TARIKE se karta hai.
Papa: generate() → Ollama API se baat karta hai
Beta: generate() → Groq API se baat karta hai (OVERRIDE!)

Papa ka prompt building talent toh wahi raha — sirf API call alag!
============================================================
"""

import json
import time
from ..config import GROQ_API_KEY, GROQ_MODEL
from .ollama_client import OllamaClient

# Groq SDK import
try:
    from groq import Groq

    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    print("⚠️ groq not installed! Run: pip install groq")


class GroqClient(OllamaClient):
    """
    Groq-powered LLM Client — OllamaClient ka smart beta! ☁️

    INHERITANCE:
    ────────────
    OllamaClient se extend karta hai.
    Prompt building methods papa se milte hain (inherit).
    Sirf API call methods override kiye hain (Groq API).

    Kya override hua:
      - __init__()                 → Groq client setup
      - generate()                 → Groq API call
      - generate_voice_response()  → Groq API call with JSON mode

    Kya inherit hua (FREE mein!):
      - build_voice_conversation_prompt()  → Wahi prompt logic
      - build_voice_retry_prompt()         → Wahi retry logic
      - _get_language_example()            → Wahi examples
    """

    def __init__(self):
        """
        Groq Client setup — API key validate karo.

        super().__init__() NAHI call kar rahe kyunki woh Ollama setup
        karega jo humein nahi chahiye. Sirf zaruri attributes set karo.

        super() kya hai?
        ────────────────
        super() = papa ka reference. super().__init__() = papa ka constructor call karo.
        But yahan hum NAHI call kar rahe kyunki papa (OllamaClient) ka __init__
        Ollama-specific kaam karta hai (base_url set karna etc.)
        Hum apna naya setup karenge (Groq API key).
        """
        # API key check
        self.api_key = GROQ_API_KEY
        self.model = GROQ_MODEL

        if not self.api_key:
            print("❌ GROQ_API_KEY not set! Set it in environment or config.py")
            print("   Get free key: https://console.groq.com")
            self.client = None
        else:
            self.client = Groq(api_key=self.api_key)
            # Mask the API key for security (sirf last 4 chars dikhao)
            masked_key = f"...{self.api_key[-4:]}" if len(self.api_key) > 4 else "****"
            print(f"✅ Groq Client ready! (Model: {self.model}, Key: {masked_key})")

    def generate(
        self, prompt: str, system_prompt: str = None, temperature: float = 0.7
    ) -> str:
        """
        Groq se jawab lo — OpenAI-compatible API.

        OpenAI-compatible kya hai?
        ─────────────────────────
        Groq ka API OpenAI jaisa hai (chat.completions.create).
        Matlab agar kal OpenAI use karna ho, toh bas client badlo!
        Prompt format same rahega.

        Socho jaise USB — ek hi plug, bahut devices kaam karein.
        OpenAI-compatible API = LLM ki USB.

        Messages format:
        ────────────────
        Ollama: {"prompt": "...", "system": "..."}  → flat format
        Groq:   [{"role": "system", ...}, {"role": "user", ...}]  → chat format

        Chat format zyada powerful hai kyunki:
        - Multi-turn conversation naturally express hoti hai
        - System/user/assistant roles clear hain
        """
        if not self.client:
            return "Error: Groq client not initialized. Set GROQ_API_KEY."

        # Messages list banao — chat format
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            start = time.perf_counter()

            # Groq API call — OpenAI-compatible format
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=1024,
            )

            duration = time.perf_counter() - start

            # response.choices[0].message.content = generated text
            # Groq always returns a list of "choices" (usually just 1)
            answer = response.choices[0].message.content.strip()
            print(f"   ⏱️ Groq response: {duration:.1f}s")
            return answer

        except Exception as e:
            print(f"   ❌ Groq error: {e}")
            return f"Error: {e}"

    def generate_voice_response(
        self,
        prompt: str,
        system_prompt: str = None,
        temperature: float = 0.7,
        timeout: int = 30,
    ) -> str:
        """
        Voice conversation ke liye Groq se JSON response lo.

        JSON MODE:
        ──────────
        Groq mein response_format={"type": "json_object"} lagao
        toh output GUARANTEED valid JSON hoga!

        Ollama se farak:
        - Ollama: "format": "json"             (payload mein)
        - Groq: response_format={"type": ...}  (parameter mein)
        Same concept, different syntax.

        Timeout parameter:
        ──────────────────
        Groq superfast hai (2-5 sec), toh timeout rarely hit hoga.
        But phir bhi fallback JSON rakhte hain — student wait na kare.
        """
        if not self.client:
            return ""

        # Messages list banao
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            start = time.perf_counter()

            # JSON mode ON — output guaranteed valid JSON
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=512,  # Voice ke liye chhota output (80 words ≈ 100-150 tokens)
                response_format={"type": "json_object"},  # ← JSON force!
            )

            duration = time.perf_counter() - start
            answer = response.choices[0].message.content.strip()

            # Token usage info (debugging ke liye)
            usage = response.usage
            print(
                f"   ⏱️ Groq voice: {duration:.1f}s "
                f"({usage.prompt_tokens} prompt + {usage.completion_tokens} completion "
                f"= {usage.total_tokens} total tokens)"
            )

            return answer

        except Exception as e:
            print(f"   ❌ Groq voice error: {e}")
            # Error pe fallback JSON — student ko kuch toh bolna chahiye!
            return json.dumps(
                {
                    "response": "That's interesting! Let me think about that.",
                    "corrections": [],
                    "follow_up_question": "Could you tell me more about what you mean?",
                }
            )

    @staticmethod
    def is_available() -> bool:
        """Groq SDK installed hai aur API key set hai ya nahi?"""
        return GROQ_AVAILABLE and bool(GROQ_API_KEY)
