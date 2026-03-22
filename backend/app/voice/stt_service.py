"""
============================================================
VOICE MODULE: STT Service — Student Ki Awaaz Samjho! 🎙️
============================================================

📖 EXPLANATION:

STT = Speech-to-Text = Awaaz ko text mein badalna.
Jaise YouTube subtitles auto-generate karta hai — woh STT hai.

Hum OpenAI ka Whisper model use kar rahe hain:
- LOCAL hai (koi internet nahi chahiye after download!)
- Open-source hai (free, no API key)
- Bahut accurate hai (even for Indian English accent)

Whisper kaise kaam karta hai?
─────────────────────────────
1. Audio file lo (MP3, WAV, WebM, etc.)
2. Audio ko 30-second chunks mein toddo
3. Har chunk ko "mel spectrogram" (sound ki image) mein badlo
4. Neural network se text predict karo
5. Saara text jod ke return karo

Model sizes:
────────────
Whisper ke multiple models hain — chhota = fast but less accurate,
bada = slow but more accurate.

Hum "base.en" use kar rahe hain kyunki:
- Sirf English chahiye (isliye .en version — faster)
- GTX 1650 pe fit ho jaata hai (~1 GB VRAM)
- Accuracy acchi hai casual conversation ke liye

Audio Length Limit kyun?
────────────────────────
Agar student 5 minute ka audio bheje toh Whisper bahut time lega!
Isliye hum 20 seconds ka limit rakhte hain.
- 20 sec = ~1-3 sentences (voice chat ke liye perfect)
- Whisper 20 sec audio ko ~2-4 sec mein transcribe karta hai

STATIC method kya hai?
──────────────────────
@staticmethod = wo method jo class ke object ke bina kaam kare.
Socho — "2+2 = 4" jaanne ke liye calculator OBJECT banana zaruri nahi,
yeh ek general fact hai. Similarly, is_available() check karta hai
ki Whisper installed hai ya nahi — object ki zarurat nahi.
============================================================
"""

import os
import time
from pathlib import Path

# Whisper import — model loading heavy hai, lazy load karenge
try:
    import whisper

    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("⚠️ openai-whisper not installed! Run: pip install openai-whisper")


# ============================================================
# STT CONFIGURATION
# ============================================================
#
# Model selection — tumhare hardware ke hisaab se choose karo.
#
# GTX 1650 (4 GB VRAM) ke liye "base.en" best hai:
# - Sirf ~140 MB download
# - ~1 GB VRAM use karta hai
# - English-only version toh aur fast hai
#
# Agar GPU nahi hai toh CPU pe bhi chalega, bas slow hoga.
# Whisper automatically GPU use karta hai agar available ho.

STT_MODEL_SIZE = "base.en"  # English-only, fast + good accuracy

# Audio constraints — student ki audio kitni lambi ho sakti hai
MAX_AUDIO_DURATION_SEC = 20  # 20 seconds max — iske baad reject
MIN_AUDIO_DURATION_SEC = 0.5  # 0.5 seconds min — isse kam = noise

# Supported audio formats
SUPPORTED_FORMATS = {".mp3", ".wav", ".webm", ".ogg", ".flac", ".m4a", ".mp4"}


# ============================================================
# STT SERVICE CLASS
# ============================================================


class STTService:
    """
    Speech-to-Text Service — audio ko text mein badlo.

    LAZY LOADING pattern:
    ─────────────────────
    Whisper model bahut bada hai (~140 MB).
    Agar server start hote hi load karein toh startup slow hoga.

    Isliye hum "lazy loading" use karte hain:
    - Server start pe sirf class banao (fast)
    - Pehli baar transcribe() call ho TAB model load karo
    - Baad mein model cached rehta hai (dobara load nahi hota)

    Socho jaise YouTube video — thumbnail pehle load hota hai (fast),
    actual video TAB load hota hai jab click karo (lazy).
    """

    def __init__(self, model_size: str = STT_MODEL_SIZE):
        """
        STT Service banao — model size set karo.

        NOTE: Model yahan load NAHI hota — sirf setting save hoti hai.
        Actual loading _load_model() mein hoga (pehli baar transcribe pe).
        """
        self.model_size = model_size
        self._model = None  # None = model abhi loaded nahi hai

        print(f"🎙️ STT Service: model={self.model_size} (will load on first use)")

    def _load_model(self):
        """
        Whisper model load karo (lazy — pehli baar hi hoga).

        _underscore prefix kya hai?
        ──────────────────────────
        Python mein _ se shuru hone wale methods "private" hote hain.
        Matlab: yeh method BAHAR se call nahi karna chahiye,
        sirf class ke andar use hota hai.

        Soch: _load_model() = kitchen ka kaam (customer nahi dekhta)
              transcribe() = serving ka kaam (customer ke liye)
        """
        if self._model is not None:
            return  # Already loaded hai, dobara mat karo

        if not WHISPER_AVAILABLE:
            raise RuntimeError("Whisper not installed!")

        print(f"   🔄 Loading Whisper model '{self.model_size}'...")
        print("   (Pehli baar download hoga ~140MB, phir cache se aayega)")

        t_start = time.perf_counter()

        # whisper.load_model() kya karta hai:
        # 1. Model file check karta hai (~/.cache/whisper/)
        # 2. Agar nahi hai toh download karta hai (sirf pehli baar)
        # 3. GPU available hai toh GPU pe load karta hai, warna CPU
        self._model = whisper.load_model(self.model_size)

        t_end = time.perf_counter()
        device = next(self._model.parameters()).device
        print(f"   ✅ Whisper loaded in {t_end - t_start:.1f}s on {device}")

    async def transcribe(self, audio_path: str) -> dict:
        """
        Audio file ko text mein badlo — yeh MAIN function hai.

        Flow:
        ─────
        1. Audio file validate karo (exists? format? size?)
        2. Model load karo (agar pehli baar hai)
        3. Whisper se transcribe karo
        4. Result return karo {text, language, duration}

        Async wrapper kyun?
        ───────────────────
        Whisper actually synchronous hai (CPU/GPU block karta hai).
        But hum isse async wrapper mein rakh rahe hain kyunki:
        - Future mein asyncio.to_thread() se non-blocking bana sakte hain
        - Baaki pipeline (TTS, API) async hai — consistent interface

        Returns:
            dict: {
                "text": "transcribed text",
                "language": "en",
                "duration_sec": 3.5,
                "processing_time_sec": 1.2,
                "success": True
            }
        """

        # ---- Step 1: Audio file validate karo ----
        validation = self._validate_audio(audio_path)
        if not validation["valid"]:
            return {
                "text": "",
                "language": "",
                "duration_sec": 0,
                "processing_time_sec": 0,
                "success": False,
                "error": validation["error"],
            }

        # ---- Step 2: Model load karo (lazy) ----
        try:
            self._load_model()
        except Exception as e:
            return {
                "text": "",
                "language": "",
                "duration_sec": 0,
                "processing_time_sec": 0,
                "success": False,
                "error": f"Model load failed: {e}",
            }

        # ---- Step 3: Transcribe karo ----
        t_start = time.perf_counter()

        try:
            # whisper.transcribe() kya karta hai:
            # 1. Audio file ko 16kHz mono audio mein convert karta hai
            # 2. 30-second windows mein todta hai
            # 3. Har window ka mel spectrogram banata hai
            # 4. Neural network se text predict karta hai
            # 5. Pura text jod ke return karta hai
            #
            # fp16=False kyunki GTX 1650 pe fp16 issues aa sakte hain
            # Agar tumhara GPU fp16 support karta hai, toh True karo
            result = self._model.transcribe(
                audio_path,
                language="en",  # English fix karo — faster + accurate
                fp16=False,  # GTX 1650 safe mode
                without_timestamps=True,  # Timestamps nahi chahiye — sirf text
            )

            t_end = time.perf_counter()
            processing_time = t_end - t_start

            # Extract text — strip whitespace
            text = result.get("text", "").strip()
            language = result.get("language", "en")

            # Audio duration calculate karo (approximate from segments)
            segments = result.get("segments", [])
            duration = segments[-1]["end"] if segments else 0

            print(f"   🎙️ STT done: '{text[:60]}...' ({processing_time:.1f}s)")

            return {
                "text": text,
                "language": language,
                "duration_sec": round(duration, 2),
                "processing_time_sec": round(processing_time, 2),
                "success": True,
                "error": None,
            }

        except Exception as e:
            t_end = time.perf_counter()
            print(f"   ❌ STT failed: {e}")
            return {
                "text": "",
                "language": "",
                "duration_sec": 0,
                "processing_time_sec": round(t_end - t_start, 2),
                "success": False,
                "error": f"Transcription failed: {e}",
            }

    def _validate_audio(self, audio_path: str) -> dict:
        """
        Audio file validate karo before processing.

        Validation kyun zaruri hai?
        ──────────────────────────
        Agar galat file Whisper ko de do toh:
        - Crash ho sakta hai
        - Bahut time waste hoga
        - Server hang ho sakta hai

        Socho jaise security check hota hai airport pe —
        pehle check karo, phir andar aane do.

        Checks:
        1. File exists hai?
        2. Format supported hai? (MP3, WAV, WebM, etc.)
        3. File size zero nahi hai?
        4. File zyada badi nahi hai? (20 sec limit)
        """

        # Check 1: File exists?
        if not audio_path or not os.path.exists(audio_path):
            return {"valid": False, "error": "Audio file not found"}

        # Check 2: Format supported?
        ext = Path(audio_path).suffix.lower()
        if ext not in SUPPORTED_FORMATS:
            return {
                "valid": False,
                "error": f"Unsupported format: {ext}. Supported: {SUPPORTED_FORMATS}",
            }

        # Check 3: File not empty?
        file_size = os.path.getsize(audio_path)
        if file_size == 0:
            return {"valid": False, "error": "Audio file is empty (0 bytes)"}

        # Check 4: File not too large?
        # Rough estimate: 1 sec MP3 ≈ 16 KB (at 128 kbps)
        # 20 sec ≈ 320 KB, but with margin let's say 5 MB max
        max_size_bytes = 5 * 1024 * 1024  # 5 MB
        if file_size > max_size_bytes:
            return {
                "valid": False,
                "error": f"Audio file too large: {file_size / 1024 / 1024:.1f} MB (max 5 MB)",
            }

        return {"valid": True, "error": None}

    def cleanup_audio(self, audio_path: str) -> bool:
        """
        Audio file delete karo — transcribe hone ke baad.

        Same concept as TTS cleanup — rough sheet wala analogy.
        Student ki audio transcribe ho gayi = kaam khatam, delete karo.
        """
        try:
            if audio_path and os.path.exists(audio_path):
                os.remove(audio_path)
                return True
            return False
        except Exception as e:
            print(f"   ⚠️ Audio cleanup failed: {e}")
            return False

    @staticmethod
    def is_available() -> bool:
        """Whisper installed hai ya nahi?"""
        return WHISPER_AVAILABLE
