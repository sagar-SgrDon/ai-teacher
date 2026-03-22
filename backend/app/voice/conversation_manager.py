"""
============================================================
VOICE MODULE: Conversation Manager — Teacher Ki Notebook 📒
============================================================

📖 EXPLANATION:

Yeh file voice teacher ka "brain" hai.
Jab student baat karta hai, yeh track karta hai:
  1. Kya baat hui (conversation history)
  2. Kya galtiyan hui (corrections list)
  3. Kitni baar same galti hui (repeated mistake tracking)
  4. Student ka level kya hai (beginner / intermediate / advanced)
  5. Abhi kaunsa mode chal raha hai (free_talk / grammar_drill / etc.)

Socho jaise ek teacher ki notebook — har class ke baad woh
likhta hai ki student ne kya seekha, kya galti ki.

ENUM kya hai?
─────────────
Enum = "choices ki list" — fixed options jinmein se ek choose karo.
Jaise dropdown mein options hoti hain — wahi cheez code mein.
Agar free text allow karo toh koi bhi kuch bhi likh dega —
"tense_error", "Tense Error", "TENSE" — tracking mushkil!
Enum se sab SAME format mein hoga.

DATACLASS kya hai?
──────────────────
Dataclass = ek shortcut jo Python deta hai "data store karne
waali class" banane ke liye. Normally __init__ likhna padta hai,
but @dataclass lagao toh Python khud bana deta hai!
============================================================
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid


# ============================================================
# ERROR TYPES — Galtiyon Ki Categories
# ============================================================
#
# Yeh FIXED categories hain — LLM ko bhi yahi use karna padega.
# Agar LLM koi random error_type bheje (jo is list mein nahi hai),
# toh hum us correction ko REJECT kar denge.
#
# Kyun fixed? Kyunki agar free text allow karo toh:
#   "tense_error", "Tense Error", "tense", "verb_tense" — sab alag!
#   Tracking mushkil ho jaati hai.
#   Fixed enum se sab ek hi format mein hoga.


class ErrorType(str, Enum):
    """
    English mistakes ki categories — strict enum.

    str inherit karna kyun zaroori hai?
    ────────────────────────────────────
    str + Enum mila ke likhne se yeh value JSON mein directly
    string ki tarah jaata hai → "tense_agreement"
    Bina str ke Enum value JSON serializable nahi hota.
    """

    TENSE_AGREEMENT = "tense_agreement"  # "I goes" → "I go"
    ARTICLE_USAGE = "article_usage"  # "give me book" → "give me a book"
    PREPOSITION = "preposition"  # "I live at India" → "I live in India"
    SUBJECT_VERB = "subject_verb_agreement"  # "He don't" → "He doesn't"
    WORD_ORDER = "word_order"  # "I yesterday went" → "I went yesterday"
    PRONOUN = "pronoun_usage"  # "Me and him went" → "He and I went"
    PLURAL_SINGULAR = "plural_singular"  # "two book" → "two books"
    VOCABULARY_CHOICE = "vocabulary_choice"  # "I am agree" → "I agree"
    SENTENCE_FRAGMENT = "sentence_fragment"  # "Because tired." → "I am tired."
    DOUBLE_NEGATIVE = (
        "double_negative"  # "I don't know nothing" → "I don't know anything"
    )
    SPELLING = "spelling"  # Spelling-related issues
    OTHER = "other"  # Jo upar kisi mein fit na ho


# ============================================================
# CORRECTION — Ek Galti Ka Record
# ============================================================
# Jab teacher galti pakadta hai, yeh ek "correction slip" banti hai
# Jaise school mein teacher red pen se galti mark karta hai,
# waise hi yeh record rakhta hai ki kya galat tha, kya sahi tha


@dataclass
class Correction:
    """
    Ek single correction ka record.

    @dataclass lagane se Python khud __init__ bana deta hai:
    c = Correction(original="I goes", corrected="I go", ...)
    Bina dataclass ke yeh sab manually likhna padta — boilerplate!
    """

    original: str  # Student ne kya bola: "I goes to market"
    corrected: str  # Sahi kya tha: "I go to the market"
    error_type: ErrorType  # Galti ki category: ErrorType.TENSE_AGREEMENT
    explanation: str  # Kyun galat: "With 'I', use base verb 'go' not 'goes'"
    turn_number: int  # Kaunse turn mein galti hui
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Dictionary mein convert karo — JSON mein bhejne ke liye"""
        return {
            "original": self.original,
            "corrected": self.corrected,
            "error_type": self.error_type.value,  # .value se string milta hai
            "explanation": self.explanation,
            "turn_number": self.turn_number,
            "timestamp": self.timestamp.isoformat(),
        }


# ============================================================
# TURN MESSAGE — Ek Bol Ka Record
# ============================================================
# Conversation mein har ek message ek "turn" hai
# Student bola = ek turn, Teacher bola = ek turn


@dataclass
class TurnMessage:
    """
    Conversation ka ek message.

    role: Kisne bola? "student" ya "teacher"
    content: Kya bola?
    turn_number: Yeh kitni-vi baari baat hai
    """

    role: str  # "student" ya "teacher"
    content: str  # Actual message text
    turn_number: int
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "content": self.content,
            "turn_number": self.turn_number,
            "timestamp": self.timestamp.isoformat(),
        }


# ============================================================
# CONVERSATION STATE — Teacher Ka Mood / Plan
# ============================================================
#
# Yeh decide karta hai ki teacher abhi KYA kar raha hai.
# Bina state ke teacher randomly kuch bhi bol dega —
# ek baar grammar, ek baar vocabulary, koi consistency nahi.
#
# STATE MACHINE kya hai?
# ─────────────────────
# Socho traffic light: RED → GREEN → YELLOW → RED
# Har state mein ek specific cheez hoti hai, aur rules hain
# ki kab kaunsa state aayega.
#
# Humara teacher bhi aise kaam karta hai:
#   free_talk → (student ne 2 baar same galti ki) → grammar_drill
#   grammar_drill → (2 sahi attempts ya 3 turns max) → free_talk
#   free_talk → (5 turns bina galti ke) → offer harder topic


@dataclass
class ConversationState:
    """
    Abhi teacher kya kar raha hai — mode, topic, aur goal.

    Modes:
      free_talk        = Bas normal baat-cheet (default)
      grammar_drill    = Specific galti ki practice (repeated mistake ke baad trigger)
      vocabulary       = Naye words seekhna
      scenario_practice = Role-play (restaurant ordering, interview, etc.)

    Turn Goals:
      teach_concept    = Naya concept samjhana
      practice         = Practice karwana
      revision_drill   = Puraani galti phir se practice
      correct_mistake  = Abhi ki galti correct karna
    """

    mode: str = "free_talk"
    current_topic: str = "general_conversation"
    turn_goal: str = "teach_concept"
    drill_turns_count: int = 0  # Grammar drill mein kitne turns ho chuke
    drill_error_type: str = ""  # Kaunsi galti ki drill chal rahi hai

    # LOOP GUARD — grammar_drill mein max 3 turns, phir force exit!
    # Warna student bore ho jaayega aur chhod dega
    MAX_DRILL_TURNS: int = 3

    def to_dict(self) -> dict:
        return {
            "mode": self.mode,
            "current_topic": self.current_topic,
            "turn_goal": self.turn_goal,
            "drill_turns_count": self.drill_turns_count,
            "drill_turns_remaining": max(
                0, self.MAX_DRILL_TURNS - self.drill_turns_count
            ),
        }


# ============================================================
# CONVERSATION SESSION — Ek Student Ki Poori Class
# ============================================================
# Jab student "Start Conversation" press karta hai, ek naya session banta hai.
# Session mein sab store hota hai — messages, corrections, state, level.
# Jaise school mein har class ka attendance register alag hota hai.

# Memory limits — context overflow se bachne ke liye
MAX_MEMORY_TURNS = 16  # Sirf last 16 turns yaad rakho
# Purane turns ka summary bana do


@dataclass
class ConversationSession:
    """
    Ek complete conversation session — student ki ek class.

    Har session mein:
      - Saare messages (sliding window — last 16)
      - Saari corrections (poori list)
      - Galtiyon ka count (per error_type)
      - Student level (auto-adjusted)
      - Conversation state (current mode/topic)

    UUID kya hai?
    ─────────────
    Universally Unique Identifier — ek aisa random ID jo KABHI repeat nahi hota.
    Har session ka unique ID hota hai taaki confuse na ho.
    Jaise Aadhaar number — har person ka alag.
    """

    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    student_level: str = "beginner"  # "beginner" | "intermediate" | "advanced"
    native_language: str = "english"  # "english" | "hinglish" | "hindi"

    # Messages — sliding window (max 16)
    messages: list = field(default_factory=list)

    # Summary — purane messages ka summary (jab 16 se zyada ho)
    summary: str = ""

    # Corrections — poori session ki saari corrections
    corrections: list = field(default_factory=list)

    # Mistake counts — har error_type kitni baar hua
    # {"tense_agreement": 3, "article_usage": 1}
    mistake_counts: dict = field(default_factory=dict)

    # State machine
    state: ConversationState = field(default_factory=ConversationState)

    # Topics covered — tracking ke liye
    topics_covered: list = field(default_factory=list)

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    current_turn: int = 0


# ============================================================
# CONVERSATION MANAGER — Saare Sessions Ka Boss
# ============================================================
# Yeh class saare active sessions ko manage karta hai.
# Jaise principal saare classes ko manage karta hai.
#
# Important methods:
#   create_session()  → Naya session shuru karo
#   add_turn()        → Student/Teacher ka message add karo
#   get_context()     → LLM ke liye conversation history do
#   track_correction() → Galti record karo + repeated check karo
#   should_add_correction() → Kya yeh correction add karni chahiye? (debounce)
#   update_state()    → State machine transitions
#   adjust_level()    → Student ka level adjust karo (error-rate se)


class ConversationManager:
    """
    Saare conversation sessions ko manage karta hai.

    Dictionary kya hai? (self.sessions)
    ──────────────────────────────────
    Dictionary = key-value pairs ka collection.
    Jaise phone book: naam → number.
    Hum session_id → session object store karte hain.
    """

    def __init__(self):
        """Constructor — empty sessions dictionary banao"""
        # session_id → ConversationSession mapping
        self.sessions: dict[str, ConversationSession] = {}
        print("✅ Conversation Manager ready!")

    # ================ SESSION MANAGEMENT ================

    def create_session(
        self, student_level: str = "beginner", native_language: str = "english"
    ) -> str:
        """
        Naya session shuru karo — jaise naya class shuru hua!

        Returns: session_id (unique ID)
        """
        session = ConversationSession(
            student_level=student_level, native_language=native_language
        )
        self.sessions[session.session_id] = session
        print(
            f"📝 New session: {session.session_id[:8]}... (level: {student_level}, lang: {native_language})"
        )
        return session.session_id

    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Session dhundho — agar nahi mili toh None return karo"""
        return self.sessions.get(session_id)

    # ================ MESSAGE MANAGEMENT ================

    def add_turn(self, session_id: str, role: str, content: str):
        """
        Conversation mein naya message add karo.

        role = "student" ya "teacher"
        content = actual message text

        Yeh method:
        1. Message add karta hai
        2. Turn counter badhata hai
        3. Agar messages > 16 ho gaye → summarize + trim (memory cap)
        """
        session = self.sessions.get(session_id)
        if not session:
            print(f"❌ Session {session_id[:8]}... nahi mili!")
            return

        session.current_turn += 1

        message = TurnMessage(
            role=role, content=content, turn_number=session.current_turn
        )
        session.messages.append(message)

        # Memory cap — agar 16 se zyada turns ho gaye
        # toh purane messages ka summary banao aur hatao
        if len(session.messages) > MAX_MEMORY_TURNS:
            self._summarize_and_trim(session)

    def _summarize_and_trim(self, session: ConversationSession):
        """
        Memory management — purane messages ka summary banao.

        Kyun zaruri hai?
        ─────────────────
        LLM ka context window LIMITED hota hai (phi3:mini ≈ 4096 tokens).
        Agar 50 messages bhejo toh context overflow ho jaayega.

        Solution: Purane messages ka ek chhota "summary" banao,
        aur sirf last 12 messages rakho.

        ABHI ke liye: simple concatenation — baad mein LLM se
        proper summary generate karwayenge.
        """
        # Purane messages (jo remove honge) — unka text join karo
        old_messages = session.messages[:-12]  # 12 rakho, baaki summarize

        summary_parts = []
        for msg in old_messages:
            summary_parts.append(f"{msg.role}: {msg.content}")

        old_summary = "\n".join(summary_parts)

        # Purane summary + naya summary jodo
        if session.summary:
            session.summary = f"{session.summary}\n---\n{old_summary}"
        else:
            session.summary = old_summary

        # Summary ko cap karo (bahut lamba na ho)
        # ~500 words max — roughly 2000 characters
        if len(session.summary) > 2000:
            session.summary = session.summary[-2000:]

        # Sirf last 12 messages rakho
        session.messages = session.messages[-12:]

    # ================ CORRECTION TRACKING ================

    def should_add_correction(
        self, session_id: str, error_type: ErrorType, original: str
    ) -> bool:
        """
        Debounce check — kya yeh correction add karni chahiye?

        DEBOUNCE kya hai?
        ─────────────────
        Socho tumhare ghar ki calling bell — agar koi 10 baar
        dabaye toh kya 10 baar chalni chahiye? Nahi!
        Pehli baar bajao, phir thoda wait karo.

        Waise hi — agar student ne same galti ki jo LAST TURN mein
        correct ki thi, toh dobara mat batao (annoying lagta hai).
        Agar 2-3 turns ke baad phir kare, TAB batao.
        """
        session = self.sessions.get(session_id)
        if not session:
            return False

        # Last turn ki corrections check karo
        last_turn = session.current_turn
        recent_corrections = [
            c
            for c in session.corrections
            if c.turn_number >= last_turn - 1  # last 1 turn mein
            and c.error_type == error_type
            and c.original.lower() == original.lower()
        ]

        # Agar last turn mein yahi correction thi → skip (debounce)
        return len(recent_corrections) == 0

    def track_correction(self, session_id: str, correction: Correction):
        """
        Correction record karo + repeated mistake count badhaao.

        Jab count >= 2 ho jaaye → state transition trigger karo:
        mode = "grammar_drill" (is galti ki practice karao)
        """
        session = self.sessions.get(session_id)
        if not session:
            return

        session.corrections.append(correction)

        # Mistake count badhao
        error_key = correction.error_type.value
        session.mistake_counts[error_key] = session.mistake_counts.get(error_key, 0) + 1

        count = session.mistake_counts[error_key]
        print(f"   📊 Mistake '{error_key}': {count} times")

        # Repeated mistake detected! → Grammar drill mode
        if count >= 2 and session.state.mode != "grammar_drill":
            print(
                f"   🔄 Repeated mistake! Switching to grammar_drill for: {error_key}"
            )
            session.state.mode = "grammar_drill"
            session.state.turn_goal = "revision_drill"
            session.state.drill_error_type = error_key
            session.state.drill_turns_count = 0

    def get_repeated_mistakes(self, session_id: str) -> list:
        """
        Woh galtiyan return karo jo 2+ baar hui hain.
        Yeh info LLM prompt mein jaayegi taaki teacher in par
        zyada dhyan de.
        """
        session = self.sessions.get(session_id)
        if not session:
            return []

        return [
            {"error_type": error_type, "count": count}
            for error_type, count in session.mistake_counts.items()
            if count >= 2
        ]

    # ================ STATE MACHINE ================

    def update_state_after_turn(self, session_id: str):
        """
        Har turn ke baad state machine update karo.

        STATE TRANSITIONS:
        ──────────────────
        1. grammar_drill mein 3 turns ho gaye → FORCE back to free_talk
           (Loop guard — student bore na ho)

        2. grammar_drill mein student ne 2 baar sahi bola → free_talk
           (Drill complete!)

        3. free_talk mein 5 turns bina galti → offer harder topic
           (Student improve kar raha hai)
        """
        session = self.sessions.get(session_id)
        if not session:
            return

        state = session.state

        # ---- LOOP GUARD: grammar drill mein max 3 turns ----
        if state.mode == "grammar_drill":
            state.drill_turns_count += 1

            if state.drill_turns_count >= state.MAX_DRILL_TURNS:
                print("   🔓 Drill loop guard triggered! Returning to free_talk")
                state.mode = "free_talk"
                state.turn_goal = "teach_concept"
                state.drill_turns_count = 0
                state.drill_error_type = ""

        # ---- Level adjustment (every 5 turns) ----
        if session.current_turn % 5 == 0 and session.current_turn > 0:
            self.adjust_level(session_id)

    def adjust_level(self, session_id: str):
        """
        Student ka level adjust karo — ERROR RATE ke basis pe.

        IMPORTANT: LLM ki assessment pe BHAROSA MAT KARO!
        LLM randomly "advanced" bol sakta hai. Error rate =
        OBJECTIVE measure jo hum khud calculate karte hain.

        Formula:
          error_rate = total corrections / total turns (last 10)
          > 0.6  → beginner (bahut galtiyan)
          > 0.3  → intermediate (kuch galtiyan)
          ≤ 0.3  → advanced (kam galtiyan)
        """
        session = self.sessions.get(session_id)
        if not session or session.current_turn < 5:
            return  # Kam se kam 5 turns ke baad hi adjust karo

        # Last 10 turns ki corrections count karo
        recent_turn_start = max(1, session.current_turn - 10)
        recent_corrections = [
            c for c in session.corrections if c.turn_number >= recent_turn_start
        ]

        total_recent_turns = min(10, session.current_turn)
        error_rate = (
            len(recent_corrections) / total_recent_turns
            if total_recent_turns > 0
            else 0
        )

        old_level = session.student_level

        if error_rate > 0.6:
            session.student_level = "beginner"
        elif error_rate > 0.3:
            session.student_level = "intermediate"
        else:
            session.student_level = "advanced"

        if old_level != session.student_level:
            print(
                f"   📈 Level changed: {old_level} → {session.student_level} (error_rate: {error_rate:.2f})"
            )

    # ================ CONTEXT BUILDING ================

    def get_context(self, session_id: str) -> str:
        """
        LLM ke liye conversation context banao.

        Yeh function SAARI relevant info ek string mein deta hai:
          - Purani conversation ka summary
          - Recent messages (last 16)
          - Current state (mode, topic, goal)
          - Repeated mistakes

        Yeh string LLM prompt mein inject hoti hai taaki teacher ko
        pata rahe ki pehle kya hua tha.
        """
        session = self.sessions.get(session_id)
        if not session:
            return ""

        parts = []

        # Summary of older conversation
        if session.summary:
            parts.append(f"CONVERSATION SUMMARY (earlier):\n{session.summary}")

        # Recent messages
        if session.messages:
            recent = []
            for msg in session.messages:
                speaker = "Student" if msg.role == "student" else "Teacher (Emma)"
                recent.append(f"{speaker}: {msg.content}")
            parts.append("RECENT CONVERSATION:\n" + "\n".join(recent))

        # Repeated mistakes
        repeated = self.get_repeated_mistakes(session_id)
        if repeated:
            mistakes_str = ", ".join(
                [f"{m['error_type']} ({m['count']}x)" for m in repeated]
            )
            parts.append(f"REPEATED MISTAKES TO ADDRESS: {mistakes_str}")

        return "\n\n".join(parts) if parts else "This is the start of the conversation."

    def get_state_for_prompt(self, session_id: str) -> dict:
        """
        LLM prompt ke liye current state return karo.
        Yeh dict directly prompt template mein inject hoga.
        """
        session = self.sessions.get(session_id)
        if not session:
            return {
                "mode": "free_talk",
                "current_topic": "general",
                "turn_goal": "teach_concept",
                "student_level": "beginner",
                "repeated_mistakes": "none",
            }

        repeated = self.get_repeated_mistakes(session_id)
        repeated_str = (
            ", ".join([f"{m['error_type']} ({m['count']}x)" for m in repeated])
            if repeated
            else "none"
        )

        return {
            "mode": session.state.mode,
            "current_topic": session.state.current_topic,
            "turn_goal": session.state.turn_goal,
            "student_level": session.student_level,
            "repeated_mistakes": repeated_str,
        }
