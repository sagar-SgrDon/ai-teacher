"""
============================================================
VOICE MODULE: TTS Service — Emma Ki Awaaz! 🎧
============================================================

📖 EXPLANATION:

TTS = Text-to-Speech = Text ko awaaz mein badalna.
Jaise Google Maps "500 meter mein left lo" bolta hai — woh TTS hai.

Hum Microsoft Edge ke neural voices use kar rahe hain:
- FREE hai (no API key needed!)
- High quality hai (robotic nahi lagta, natural lagta hai)
- Bahut voices available hain (male, female, different accents)

edge-tts kaise kaam karta hai?
──────────────────────────────
1. Text bhejo → Microsoft ke servers pe request jaati hai
2. Server neural network se audio generate karta hai
3. Audio (MP3) wapas aata hai → file mein save karo

ASYNC kyun zaruri hai?
──────────────────────
edge-tts ASYNC library hai (await use karta hai).
Iska matlab — jab tak audio generate ho raha hai,
server doosre kaam kar sakta hai (doosre students ki requests).

Agar sync hota toh ek student ka TTS hone tak
POORA server block ho jaata — baaki sab wait karte!

tempfile kya hai?
─────────────────
Temporary files — OS ke temp folder mein banti hain.
Hum audio generate karke bhejte hain, phir delete kar dete hain.
Kyunki audio ko permanently store karne ki zarurat nahi —
student ne sun liya, bas kaam khatam.

Socho jaise exam hall mein rough sheet dete hain —
use karo, phir wapas de do. Ghar nahi le jaate.
============================================================
"""

import os
import uuid
import tempfile
from pathlib import Path
from typing import Optional

# edge-tts import
try:
    import edge_tts

    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False
    print("⚠️ edge-tts not installed! Run: pip install edge-tts")


# ============================================================
# VOICE CONFIGURATION — Emma Ki Settings
# ============================================================
#
# Microsoft Edge ke paas 300+ voices hain!
# Hum Emma ke liye ek natural female American voice use karenge.
#
# Voice naming pattern: "LANGUAGE-COUNTRY-NameNeural"
# en-US = English-United States
# en-GB = English-United Kingdom
# en-IN = English-India
#
# Rate = speed ("+10%" = thoda fast, "-10%" = thoda slow)
# Pitch = high/low voice ("+5Hz" = thoda high pitch)

# Primary voice — Emma ke liye (natural, friendly)
EMMA_VOICE = "en-US-JennyNeural"

# Voice per native language — Hinglish ke liye Indian English voice
VOICE_BY_LANGUAGE = {
    "english": "en-US-JennyNeural",
    "hinglish": "en-IN-NeerjaNeural",  # Indian English — Hinglish mein natural lagegi
    "hindi": "hi-IN-SwaraNeural",  # Hindi female voice
}

# Backup voices — agar primary fail ho
BACKUP_VOICES = [
    "en-US-AriaNeural",  # Another natural female
    "en-GB-SoniaNeural",  # British female
    "en-US-MichelleNeural",  # Warm female
]

# Speech settings — teacher ke liye thoda slow aur clear
SPEECH_RATE = "-5%"  # 5% slow — teacher naturally slow bolta hai
SPEECH_PITCH = "+0Hz"  # Normal pitch — no change
SPEECH_VOLUME = "+0%"  # Normal volume

# Audio settings
AUDIO_FORMAT = "mp3"  # MP3 format — widely supported, small size
TEMP_DIR = None  # None = OS ka temp folder use karo


# ============================================================
# TTS SERVICE CLASS
# ============================================================


class TTSService:
    """
    Text-to-Speech Service — text ko audio mein badlo.

    CLASS kya hai? (Quick recap)
    ───────────────────────────
    Class = Blueprint. Object = Bhara hua blueprint.
    TTSService class hai, tts = TTSService() object hai.

    Hum class isliye use kar rahe hain kyunki:
    - Settings (voice, rate, pitch) ek baar set karo, baar baar use karo
    - Temp directory management ek jagah rahe
    - Future mein caching add kar sakten hain
    """

    def __init__(
        self,
        voice: str = EMMA_VOICE,
        rate: str = SPEECH_RATE,
        pitch: str = SPEECH_PITCH,
        volume: str = SPEECH_VOLUME,
        temp_dir: Optional[str] = TEMP_DIR,
    ):
        """
        TTS Service banao — voice aur settings set karo.

        Parameters:
        ──────────
        voice   : Kaunsi voice use karni hai (default: Emma = Jenny)
        rate    : Speed ("+10%" = fast, "-10%" = slow)
        pitch   : High/low voice ("+5Hz" = high)
        volume  : Loudness ("+10%" = loud)
        temp_dir: Temporary files kahan rakhni hain (None = OS default)
        """
        self.voice = voice
        self.rate = rate
        self.pitch = pitch
        self.volume = volume

        # Temp directory setup
        if temp_dir:
            self.temp_dir = Path(temp_dir)
            self.temp_dir.mkdir(parents=True, exist_ok=True)
        else:
            # OS ke temp folder use karo (Windows: C:\Users\...\AppData\Local\Temp)
            self.temp_dir = Path(tempfile.gettempdir()) / "ai_teacher_tts"
            self.temp_dir.mkdir(parents=True, exist_ok=True)

        print(f"🎧 TTS Service: voice={self.voice}, rate={self.rate}")
        print(f"   Temp dir: {self.temp_dir}")

    async def synthesize(self, text: str) -> Optional[str]:
        """
        Main function — text ko audio file mein badlo.

        async/await kya hai? (Deep dive)
        ────────────────────────────────
        Normal function: kaam shuru → kaam khatam → return
        Async function: kaam shuru → WAIT (network call) → kaam khatam → return

        "await" ka matlab: "yeh step time lega,
        iske wait mein doosra kaam kar lo"

        Socho jaise restaurant mein:
        - Waiter order deta hai kitchen mein (async call)
        - Kitchen mein khana ban raha hai (await — wait)
        - Tab tak waiter doosre table ki service karta hai!
        - Khana ready → waiter le jaata hai → done!

        Parameters:
            text: Jo bolna hai (Emma ka response)

        Returns:
            str: Audio file ka path (MP3)
            None: Agar kuch galat hua
        """

        if not EDGE_TTS_AVAILABLE:
            print("❌ edge-tts not available!")
            return None

        if not text or not text.strip():
            print("⚠️ Empty text — nothing to speak!")
            return None

        # Unique filename banao — har audio ka alag naam
        # uuid4() = random unique ID (collision impossible)
        filename = f"emma_{uuid.uuid4().hex[:12]}.{AUDIO_FORMAT}"
        output_path = str(self.temp_dir / filename)

        try:
            # ---- edge-tts Communicate object banao ----
            # Yeh object Microsoft ke servers se baat karega
            communicate = edge_tts.Communicate(
                text=text,
                voice=self.voice,
                rate=self.rate,
                pitch=self.pitch,
                volume=self.volume,
            )

            # ---- Audio generate karo aur save karo ----
            # await = "yeh network call hai, wait karo but block mat karo"
            await communicate.save(output_path)

            # Check: file actually bani ya nahi?
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                size_kb = os.path.getsize(output_path) / 1024
                print(f"   🎧 TTS done: {filename} ({size_kb:.1f} KB)")
                return output_path
            else:
                print(f"   ❌ TTS file empty or missing: {output_path}")
                return None

        except Exception as e:
            print(f"   ❌ TTS failed: {e}")

            # ---- Backup voice try karo ----
            # Agar primary voice fail ho, toh backup try karo
            return await self._try_backup_voices(text, output_path)

    async def _try_backup_voices(self, text: str, output_path: str) -> Optional[str]:
        """
        Primary voice fail hui → backup voices try karo.

        Yeh "graceful degradation" pattern hai:
        Plan A fail? → Plan B try karo → Plan C try karo → Give up

        Socho jaise AC band ho gaye:
        Plan A: AC → Fail
        Plan B: Cooler → Fail
        Plan C: Fan → Works! (at least kuch toh hai)
        """
        for backup_voice in BACKUP_VOICES:
            try:
                print(f"   🔄 Trying backup voice: {backup_voice}")

                communicate = edge_tts.Communicate(
                    text=text,
                    voice=backup_voice,
                    rate=self.rate,
                    pitch=self.pitch,
                    volume=self.volume,
                )

                await communicate.save(output_path)

                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    print(f"   ✅ Backup voice worked: {backup_voice}")
                    return output_path

            except Exception as e:
                print(f"   ❌ Backup voice {backup_voice} failed: {e}")
                continue

        print("   ❌ All voices failed!")
        return None

    def cleanup_file(self, file_path: str) -> bool:
        """
        Audio file delete karo — use hone ke baad.

        Kyun delete karna hai?
        ─────────────────────
        Temp files hain — student ne sun liya, ab zarurat nahi.
        Agar delete na karein toh disk bhar jaayegi!

        Socho jaise restaurant mein plate use hone ke baad dhote hain —
        pile up nahi karte.

        Returns:
            True: Delete successful
            False: Kuch problem aayi (file already deleted, etc.)
        """
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            print(f"   ⚠️ Cleanup failed for {file_path}: {e}")
            return False

    def cleanup_all(self) -> int:
        """
        Saari temp audio files delete karo.

        Yeh function server shutdown ya periodic cleanup mein use hota hai.
        Returns: kitni files delete hui
        """
        count = 0
        try:
            for file in self.temp_dir.glob(f"emma_*.{AUDIO_FORMAT}"):
                try:
                    file.unlink()
                    count += 1
                except Exception:
                    pass
        except Exception as e:
            print(f"   ⚠️ Cleanup all failed: {e}")

        if count > 0:
            print(f"   🧹 Cleaned up {count} temp audio files")

        return count

    async def get_available_voices(self, language: str = "en") -> list:
        """
        Available voices ki list lo — filter by language.

        Yeh debugging aur voice selection ke liye useful hai.
        Sabse popular English voices dikhata hai.

        Parameters:
            language: "en" for English, "hi" for Hindi, etc.

        Returns:
            List of voice dicts with name, gender, locale
        """
        if not EDGE_TTS_AVAILABLE:
            return []

        try:
            voices = await edge_tts.list_voices()

            # Filter by language
            filtered = [
                {
                    "name": v["ShortName"],
                    "gender": v["Gender"],
                    "locale": v["Locale"],
                    "friendly_name": v.get("FriendlyName", v["ShortName"]),
                }
                for v in voices
                if v["Locale"].startswith(language)
            ]

            return filtered

        except Exception as e:
            print(f"   ❌ Failed to list voices: {e}")
            return []

    @staticmethod
    def is_available() -> bool:
        """edge-tts installed hai ya nahi?"""
        return EDGE_TTS_AVAILABLE

    def set_voice_for_language(self, native_language: str):
        """
        Native language ke hisaab se voice change karo.

        en-IN-NeerjaNeural = Indian English voice — Hinglish mein natural!
        hi-IN-SwaraNeural = Hindi voice — Hindi explanations ke liye.
        """

        new_voice = VOICE_BY_LANGUAGE.get(native_language, EMMA_VOICE)
        if new_voice != self.voice:
            self.voice = new_voice
            print(f"   🎧 TTS voice changed to: {self.voice} (for {native_language})")
