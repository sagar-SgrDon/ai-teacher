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

DUAL MODEL STRATEGY:
────────────────────
Free plan mein har model ki daily limit hoti hai (RPD).
Agar ek model ki limit khatam ho jaye toh?

Solution: DO models use karo!
  Primary:  llama-3.3-70b-versatile  → Best quality (1K RPD)
  Fallback: llama-3.1-8b-instant     → More quota (14.4K RPD!)

Jab primary model rate limit de → automatically fallback pe switch!
Total daily capacity: 1K + 14.4K = 15.4K requests! 💪

AUTO-FALLBACK kaise kaam karta hai?
───────────────────────────────────
1. Primary model se request karo
2. Agar 429 (RateLimitError) aaye → fallback model try karo
3. Fallback kaam kare → usse continue karo
4. Dono fail → error return karo

Socho jaise highway pe:
  - Primary = Expressway (fast, but toll limit)
  - Fallback = Service road (thoda slow, but always available)
  - Agar expressway band ho → automatically service road pe aao!

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
from ..config import GROQ_API_KEY, GROQ_MODEL, GROQ_FALLBACK_MODEL
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

    DUAL MODEL + AUTO-FALLBACK:
    ───────────────────────────
    Primary:  llama-3.3-70b-versatile  (best quality, 1K RPD)
    Fallback: llama-3.1-8b-instant     (decent, 14.4K RPD!)

    Jab primary rate-limited ho → auto-switch to fallback.
    Student ko koi farak nahi padta — seamless experience!

    INHERITANCE:
    ────────────
    OllamaClient se extend karta hai.
    Prompt building methods papa se milte hain (inherit).
    Sirf API call methods override kiye hain (Groq API).

    Kya override hua:
      - __init__()                 → Groq client setup (dual model)
      - generate()                 → Groq API call + auto-fallback
      - generate_voice_response()  → Groq API call + auto-fallback + JSON mode

    Kya inherit hua (FREE mein!):
      - build_voice_conversation_prompt()  → Wahi prompt logic
      - build_voice_retry_prompt()         → Wahi retry logic
      - _get_language_example()            → Wahi examples
    """

    def __init__(self):
        """
        Groq Client setup — API key validate karo, dual models configure karo.

        super().__init__() NAHI call kar rahe kyunki woh Ollama setup
        karega jo humein nahi chahiye. Sirf zaruri attributes set karo.

        Dual model setup:
        ─────────────────
        self.model          = Primary (70B, best quality)
        self.fallback_model = Fallback (8B, high quota)
        self._active_model  = Currently active model (starts with primary)
        self._using_fallback = Track if we switched to fallback
        """
        # API key check
        self.api_key = GROQ_API_KEY
        self.model = GROQ_MODEL  # Primary: llama-3.3-70b-versatile
        self.fallback_model = GROQ_FALLBACK_MODEL  # Fallback: llama-3.1-8b-instant

        # Active model tracking
        # _underscore = private variable — bahar se mat chhedo!
        self._active_model = self.model  # Start with primary
        self._using_fallback = False  # Fallback pe hain ya nahi

        if not self.api_key:
            print("❌ GROQ_API_KEY not set! Set it in .env file")
            print("   Get free key: https://console.groq.com")
            self.client = None
        else:
            self.client = Groq(api_key=self.api_key)
            # Mask the API key for security (sirf last 4 chars dikhao)
            masked_key = f"...{self.api_key[-4:]}" if len(self.api_key) > 4 else "****"
            print(f"✅ Groq Client ready! (Key: {masked_key})")
            print(f"   🥇 Primary:  {self.model}")
            print(f"   🥈 Fallback: {self.fallback_model}")

    def _call_groq(
        self, messages, model, temperature=0.7, max_tokens=1024, json_mode=False
    ):
        """
        Internal method — actual Groq API call.

        _underscore prefix = PRIVATE method
        ───────────────────────────────────
        Yeh method sirf class ke andar use hota hai.
        Bahar se call nahi karna chahiye.

        DRY Principle (Don't Repeat Yourself):
        ─────────────────────────────────────
        generate() aur generate_voice_response() dono mein same
        Groq API call hoti hai. Toh ek common method banao!

        Socho jaise kitchen mein:
          - Dal aur sabzi dono ke liye tadka same hota hai
          - Toh tadka ka ek alag function banao (reuse!)
          - Sirf flavor (parameters) alag hota hai

        Parameters:
            messages    : Chat messages [{role, content}, ...]
            model       : Which model to use
            temperature : Creativity (0.7 = balanced)
            max_tokens  : Max output length
            json_mode   : Force JSON output?

        Returns:
            str: Model ka response text

        Raises:
            Exception: Koi bhi error (rate limit, network, etc.)
        """
        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        start = time.perf_counter()
        response = self.client.chat.completions.create(**kwargs, timeout=10)
        duration = time.perf_counter() - start

        answer = response.choices[0].message.content.strip()

        # Token usage log (debugging ke liye helpful)
        usage = response.usage
        model_short = model.split("/")[-1]  # Long model names chhota karo
        print(
            f"   ⏱️ Groq [{model_short}]: {duration:.1f}s ({usage.total_tokens} tokens)"
        )

        return answer

    def _call_with_fallback(
        self, messages, temperature=0.7, max_tokens=1024, json_mode=False
    ):
        """
        Smart API call — primary try karo, fail ho toh fallback pe jao.

        AUTO-FALLBACK LOGIC:
        ────────────────────
        1. Active model se try karo (usually primary)
        2. Agar RateLimitError (429) aaye:
           a. Agar primary tha → fallback pe switch karo, retry karo
           b. Agar fallback bhi fail → error raise karo
        3. Koi aur error → directly raise karo

        HTTP 429 kya hai?
        ─────────────────
        429 = "Too Many Requests"
        Server bol raha hai: "Bhai, bahut requests bhej di.
        Thoda ruk, ya koi aur model use kar."

        Hum rukte nahi — dusre model pe switch kar lete hain! 🔄

        Parameters: same as _call_groq()
        Returns: str (model response)
        """
        try:
            # Step 1: Active model se try karo
            return self._call_groq(
                messages, self._active_model, temperature, max_tokens, json_mode
            )

        except Exception as e:
            error_str = str(e).lower()

            # Step 2: Rate limit detect karo
            # "rate_limit" ya "429" ya "limit" — koi bhi indicator
            is_rate_limit = (
                "rate_limit" in error_str
                or "429" in error_str
                or "limit" in error_str
                or "resource_exhausted" in error_str
            )

            is_timeout_or_slow = (
                "timeout" in error_str
                or "timed out" in error_str
                or "connection" in error_str
            )

            if (
                is_rate_limit or is_timeout_or_slow
            ) and self._active_model != self.fallback_model:
                # Primary rate-limited → switch to fallback!
                print(
                    f"   ⚠️ {self._active_model} rate-limited! Switching to fallback..."
                )
                self._active_model = self.fallback_model
                self._using_fallback = True

                try:
                    # Step 3: Fallback se retry karo
                    return self._call_groq(
                        messages, self._active_model, temperature, max_tokens, json_mode
                    )
                except Exception as fallback_error:
                    print(f"   ❌ Fallback also failed: {fallback_error}")
                    raise fallback_error
            else:
                # Not a rate limit error, or already on fallback
                raise e

    def generate(
        self, prompt: str, system_prompt: str = None, temperature: float = 0.7
    ) -> str:
        """
        Groq se jawab lo — auto-fallback ke saath.

        OpenAI-compatible kya hai?
        ─────────────────────────
        Groq ka API OpenAI jaisa hai (chat.completions.create).
        Matlab agar kal OpenAI use karna ho, toh bas client badlo!
        Prompt format same rahega.

        Messages format:
        ────────────────
        Ollama: {"prompt": "...", "system": "..."}  → flat format
        Groq:   [{"role": "system", ...}, {"role": "user", ...}]  → chat format
        """
        if not self.client:
            return "Error: Groq client not initialized. Set GROQ_API_KEY in .env"

        # Messages list banao — chat format
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            return self._call_with_fallback(messages, temperature, max_tokens=1024)
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
        Voice conversation ke liye Groq se JSON response lo — auto-fallback ke saath.

        JSON MODE:
        ──────────
        response_format={"type": "json_object"} lagao
        toh output GUARANTEED valid JSON hoga!

        Auto-fallback:
        ──────────────
        Primary (70B) rate-limited? → Fallback (8B) pe switch!
        Student ko pata bhi nahi chalega — response aata rahega.
        """
        if not self.client:
            return ""

        # Messages list banao
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            return self._call_with_fallback(
                messages, temperature, max_tokens=512, json_mode=True
            )
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

    def get_active_model(self) -> str:
        """
        Currently kaunsa model active hai?
        Debugging aur logging ke liye useful.
        """
        status = "🥈 FALLBACK" if self._using_fallback else "🥇 PRIMARY"
        return f"{self._active_model} ({status})"

    @staticmethod
    def is_available() -> bool:
        """Groq SDK installed hai aur API key set hai ya nahi?"""
        return GROQ_AVAILABLE and bool(GROQ_API_KEY)
