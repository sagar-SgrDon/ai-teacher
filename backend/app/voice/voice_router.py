"""
============================================================
VOICE MODULE: Voice Router — Sab Ko Jodne Waala! 🔌
============================================================

📖 EXPLANATION:

Yeh file poore voice module ka "WAITER" hai.
Waiter khud khana nahi banata (LLM), crockery nahi dhota (parser),
bill nahi banata (logger) — but sab ko COORDINATE karta hai.

Flow:
1. Student ka message aaya (text ya audio)
2. RAG se teaching material dhundho
3. Conversation history + state lao
4. LLM se structured JSON jawab lo
5. JSON parse + validate karo
6. Corrections track karo + state update
7. Sab log karo (JSONL)
8. Response bhejo!

APIRouter kya hai?
──────────────────
FastAPI mein endpoints ko GROUPS mein rakhne ka tarika.
Jaise school mein classes hoti hain (English class, Maths class),
waise hi endpoints ke groups hote hain (/voice/..., /ask/...).

router = APIRouter() → ek naya group banao
@router.post("/start") → is group mein endpoint add karo
app.include_router(router, prefix="/voice") → main app mein mount karo

Final URL ban jayega: /voice/start

Dependency Injection kya hai?
────────────────────────────
Yeh function ko BAHAR se zaruri cheezein dene ka pattern hai.
Restaurant mein waiter ko kitchen access diya jaata hai (woh khud nahi banata).
Waise hi, voice_router ko retriever aur llm_client BAHAR se milte hain.
============================================================
"""

import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from fastapi.responses import FileResponse

# ---- Apne modules import karo ----
from .conversation_manager import ConversationManager
from .llm_parser import (
    parse_llm_response_with_retry,
    normalize_text,
    dict_to_correction,
)
from .logger import VoiceLogger


# ============================================================
# ROUTER + COMPONENTS BANAO
# ============================================================
#
# APIRouter = endpoints ka group — /voice/... ke saare endpoints
# ConversationManager = sessions manage karo
# VoiceLogger = logging karo
#
# retriever aur llm_client BAAD mein set honge (main.py startup mein)
# Kyun? Kyunki woh heavy objects hain (model load karna padta hai)
# Server start hone pe set honge, pehle nahi.

router = APIRouter(tags=["Voice Conversation"])

# Yeh objects yahan banenge — lightweight hain
conversation_manager = ConversationManager()
voice_logger = VoiceLogger()

# Yeh BAAD mein set honge — main.py se (dependency injection)
_retriever = None
_llm_client = None
_tts_service = None


def init_voice_components(retriever, llm_client, tts_service=None):
    """
    Main.py se call hoga — heavy components set karo.

    Kyun alag function hai?
    ──────────────────────
    retriever aur llm_client server startup pe bante hain (heavy!).
    voice_router.py import hote waqt yeh available nahi hote.
    Isliye ek "init" function hai jo BAAD mein call hota hai.

    Socho — restaurant subah khulta hai, waiter pehle aata hai,
    phir kitchen ready hota hai, phir waiter ko access milta hai.
    """
    global _retriever, _llm_client, _tts_service
    _retriever = retriever
    _llm_client = llm_client
    _tts_service = tts_service
    print("✅ Voice Router: Components connected!")
    if _tts_service:
        print("   🎧 TTS: enabled")


# ============================================================
# REQUEST / RESPONSE MODELS (Pydantic)
# ============================================================
#
# Pydantic models = "forms" — define karo ki request/response
# mein kya data aa sakta hai aur kya jaayega.
# FastAPI automatically validate karega — galat data = instant error!
#
# Optional kya hai?
# ─────────────────
# Optional[str] = "yeh field de bhi sakte ho, nahi bhi."
# Bina Optional ke sab fields REQUIRED hain.


class StartSessionRequest(BaseModel):
    """Session shuru karne ka form."""

    student_level: str = "beginner"  # Default beginner
    native_language: str = "english"  # "english" | "hinglish" | "hindi"


class StartSessionResponse(BaseModel):
    """Session shuru hone ka response."""

    session_id: str
    student_level: str
    message: str


class TextTalkRequest(BaseModel):
    """Text se baat karne ka form (voice ka fallback)."""

    session_id: str  # Kaunsi session mein baat kar rahe ho
    text: str  # Student ne kya likha/bola


class CorrectionResponse(BaseModel):
    """Ek correction ka response format."""

    original: str
    corrected: str
    error_type: str
    explanation: str


class TalkResponse(BaseModel):
    """Voice/text talk ka response — sab kuch ek jagah."""

    teacher_response: str
    follow_up: str
    corrections: list  # List of CorrectionResponse dicts
    latency: dict  # {"stt_ms": 0, "llm_ms": X, "tts_ms": 0, "total_ms": X}
    session_state: dict  # {"mode": "free_talk", "level": "beginner", ...}
    turn_number: int
    audio_url: str = ""  # TTS audio URL — empty agar TTS disabled/failed


# ============================================================
# ENDPOINT 1: Start Session — Naya Class Shuru Karo!
# ============================================================


@router.post("/start", response_model=StartSessionResponse)
async def start_session(request: StartSessionRequest):
    """
    POST /voice/start

    Naya voice conversation session shuru karo.
    Jaise class mein pehle attendance register mein naam likho,
    phir padhai shuru.

    Input:  { "student_level": "beginner" }
    Output: { "session_id": "abc-123...", "student_level": "beginner",
              "message": "..." }

    async kyun hai?
    ───────────────
    FastAPI mein async functions better performance deti hain.
    Multiple students ek saath connect ho sakte hain — ek ka wait
    doosre ko block nahi karega.
    """

    session_id = conversation_manager.create_session(
        request.student_level, request.native_language
    )

    # Logger mein session start record karo
    voice_logger.log_session_start(session_id, request.student_level)

    # Greeting language ke hisaab se set karo
    greetings = {
        "hinglish": "Hi! Main Emma hoon, tumhari English teacher. Chalo practice shuru karte hain! Batao, aaj tumhara din kaisa raha?",
        "hindi": "नमस्ते! मैं Emma हूँ, आपकी English teacher। चलिए practice शुरू करते हैं! बताइए, आज आपका दिन कैसा रहा?",
        "english": "Hi! I'm Emma, your English teacher. Let's start practicing! Tell me about your day.",
    }
    greeting = greetings.get(request.native_language, greetings["english"])

    return StartSessionResponse(
        session_id=session_id,
        student_level=request.student_level,
        message=greeting,
    )


# ============================================================
# ENDPOINT 2: Text Talk — Text Se Baat Karo! (CORE ENDPOINT)
# ============================================================
#
# YEH SABSE IMPORTANT ENDPOINT HAI!
# Poori voice logic pehle TEXT mein validate karenge.
# Baad mein STT + TTS plug karke /voice/talk banayenge.


@router.post("/talk/text", response_model=TalkResponse)
async def talk_text(request: TextTalkRequest):
    """
    POST /voice/talk/text

    Student ka text message lo → Teacher Emma ka structured response do.

    POORA FLOW:
    1. Session validate karo
    2. Text normalize karo (lowercase, cleanup)
    3. Empty check karo (silence handling)
    4. RAG se teaching material dhundho
    5. Conversation context lao (history + state)
    6. LLM se JSON response lo
    7. JSON parse + validate karo (retry if needed)
    8. Corrections track karo (with debounce)
    9. State machine update karo
    10. Sab log karo
    11. Response bhejo!

    Yeh 11 steps hain — but har step simple hai.
    Socho recipe follow kar rahe ho — step by step, easy!
    """

    t_start = time.perf_counter()

    # ---- Step 1: Session validate ----
    session = conversation_manager.get_session(request.session_id)
    if not session:
        raise HTTPException(
            status_code=404, detail="Session nahi mili! Pehle /voice/start call karo."
        )

    # ---- Step 2: Text normalize ----
    student_text = normalize_text(request.text)

    # ---- Step 3: Empty/silence handling ----
    # Agar student ne kuch nahi bola (ya Whisper ne empty return kiya)
    if not student_text:
        return TalkResponse(
            teacher_response="I didn't catch that. Could you please say that again?",
            follow_up="What would you like to talk about today?",
            corrections=[],
            latency={"stt_ms": 0, "llm_ms": 0, "tts_ms": 0, "total_ms": 0},
            session_state=session.state.to_dict(),
            turn_number=session.current_turn,
        )

    # ---- Step 4: Student ka message conversation mein add karo ----
    conversation_manager.add_turn(request.session_id, "student", student_text)

    # ---- Step 5: RAG se teaching material dhundho ----
    # top_k=2 aur ~400 token cap (as per our plan)
    rag_context = ""

    if _retriever:
        try:
            search_results = _retriever.search(
                query=student_text,
                teacher_type="english",
                top_k=2,  # Plan: top_k=2, cap ~400 tokens
            )
            if search_results:
                rag_context = _retriever.format_context(search_results)
                # Token cap: ~400 tokens ≈ ~1600 characters
                if len(rag_context) > 1600:
                    rag_context = rag_context[:1600]
        except Exception as e:
            print(f"   ⚠️ RAG search failed: {e}")
            rag_context = ""

    # ---- Step 6: Conversation context banao ----
    conversation_context = conversation_manager.get_context(request.session_id)
    state = conversation_manager.get_state_for_prompt(request.session_id)

    # ---- Step 7: LLM se response lo ----
    t_llm_start = time.perf_counter()

    if not _llm_client:
        raise HTTPException(
            status_code=503, detail="LLM client not initialized! Server restart karo."
        )

    # Session se native_language lo
    native_language = (
        session.native_language if hasattr(session, "native_language") else "english"
    )
    # Prompt banao
    prompt, system_prompt = _llm_client.build_voice_conversation_prompt(
        student_message=student_text,
        conversation_context=conversation_context,
        rag_context=rag_context,
        state=state,
        native_language=native_language,
    )

    # LLM call (JSON mode, 60s timeout)
    raw_llm_output = _llm_client.generate_voice_response(
        prompt=prompt, system_prompt=system_prompt, temperature=0.7, timeout=60
    )

    t_llm_end = time.perf_counter()
    llm_ms = round((t_llm_end - t_llm_start) * 1000)

    # ---- Step 8: JSON parse + validate (with retry) ----
    def retry_func(student_msg):
        """
        Retry function — stricter prompt se LLM ko dobara call karo.

        Closure kya hai?
        ────────────────
        Yeh function ANDAR define hua hai lekin BAHAR ke variables
        (_llm_client) use kar sakta hai. Isko "closure" kehte hain.
        Socho jaise ghar ke andar ho but window se bahar dekh sakte ho.
        """
        retry_prompt, retry_system = _llm_client.build_voice_retry_prompt(student_msg)
        return _llm_client.generate_voice_response(
            prompt=retry_prompt,
            system_prompt=retry_system,
            temperature=0.5,  # Retry mein kam creativity = zyada predictable
            timeout=30,  # Retry mein kam time (already wait kar chuke)
        )

    parsed = parse_llm_response_with_retry(
        raw_text=raw_llm_output, retry_func=retry_func, student_message=student_text
    )

    # ---- Step 9: Corrections track karo (with debounce) ----
    tracked_corrections = []

    for corr_dict in parsed.corrections:
        # Dict → Correction object
        correction_obj = dict_to_correction(corr_dict, session.current_turn)

        if correction_obj is None:
            continue

        # Debounce check — kya yeh last turn mein bhi aayi thi?
        should_add = conversation_manager.should_add_correction(
            request.session_id, correction_obj.error_type, correction_obj.original
        )

        if should_add:
            conversation_manager.track_correction(request.session_id, correction_obj)
            tracked_corrections.append(corr_dict)
        else:
            print(f"   🔕 Debounced correction: {corr_dict['original']}")

    # ---- Step 10: Teacher ka response conversation mein add karo ----
    conversation_manager.add_turn(
        request.session_id,
        "teacher",
        parsed.tts_text,  # merged response + follow_up
    )

    # ---- Step 11: State machine update ----
    conversation_manager.update_state_after_turn(request.session_id)

    # Set TTS voice based on native language
    if _tts_service and native_language != "english":
        _tts_service.set_voice_for_language(native_language)

    # ---- Step 12: TTS — Emma ki awaaz banao! ----
    # Teacher ka response + follow-up merge karke audio banao
    # parsed.tts_text already has merged text (response + follow_up)
    tts_ms = 0
    audio_url = ""

    if _tts_service and _tts_service.is_available():
        try:
            t_tts_start = time.perf_counter()
            audio_path = await _tts_service.synthesize(parsed.tts_text)
            t_tts_end = time.perf_counter()
            tts_ms = round((t_tts_end - t_tts_start) * 1000)

            if audio_path:
                # Filename extract karo path se
                import os

                audio_filename = os.path.basename(audio_path)
                audio_url = f"/voice/audio/{audio_filename}"
        except Exception as e:
            print(f"   ⚠️ TTS failed (non-blocking): {e}")

    # ---- Step 13: Latency calculate karo ----
    t_end = time.perf_counter()
    total_ms = round((t_end - t_start) * 1000)

    latency = {
        "stt_ms": 0,  # Text mode — no STT
        "llm_ms": llm_ms,
        "tts_ms": tts_ms,  # Text mode — no TTS
        "total_ms": total_ms,
    }

    # ---- Step 14: Log everything ----
    session_state = {
        "mode": session.state.mode,
        "student_level": session.student_level,
        "topic": session.state.current_topic,
        "turn_goal": session.state.turn_goal,
    }

    voice_logger.log_turn(
        session_id=request.session_id,
        turn_number=session.current_turn,
        student_text=student_text,
        teacher_response=parsed.response,
        follow_up=parsed.follow_up_question,
        corrections=tracked_corrections,
        latency=latency,
        session_state=session_state,
        error=None if parsed.parse_success else "JSON parse used fallback",
    )

    # ---- Step 15: Response bhejo! ----
    return TalkResponse(
        teacher_response=parsed.response,
        follow_up=parsed.follow_up_question,
        corrections=tracked_corrections,
        latency=latency,
        session_state=session_state,
        turn_number=session.current_turn,
        audio_url=audio_url,
    )


# ============================================================
# ENDPOINT 3: History — Poori Conversation Dekho
# ============================================================


@router.get("/history/{session_id}")
async def get_history(session_id: str):
    """
    GET /voice/history/{session_id}

    Poori conversation history return karo —
    messages + corrections + stats.

    Path parameter kya hai? ({session_id})
    ─────────────────────────────────────
    URL ke andar variable — /voice/history/abc-123
    FastAPI automatically "abc-123" ko session_id mein daal deta hai.
    Socho jaise lockers mein number hota hai — number se locker kholo.
    """

    session = conversation_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session nahi mili!")

    return {
        "session_id": session_id,
        "student_level": session.student_level,
        "total_turns": session.current_turn,
        "state": session.state.to_dict(),
        "messages": [msg.to_dict() for msg in session.messages],
        "summary": session.summary,
    }


# ============================================================
# ENDPOINT 4: Corrections — Galtiyon Ka Report Card
# ============================================================


@router.get("/corrections/{session_id}")
async def get_corrections(session_id: str):
    """
    GET /voice/corrections/{session_id}

    Session ki saari corrections return karo —
    grouped by error_type with counts.

    Yeh "report card" jaisa hai — kaunsi galti kitni baar hui.
    """

    session = conversation_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session nahi mili!")

    # Corrections ko error_type se group karo
    grouped = {}
    for corr in session.corrections:
        error_key = corr.error_type.value
        if error_key not in grouped:
            grouped[error_key] = []
        grouped[error_key].append(corr.to_dict())

    return {
        "session_id": session_id,
        "total_corrections": len(session.corrections),
        "mistake_counts": session.mistake_counts,
        "corrections_by_type": grouped,
        "repeated_mistakes": conversation_manager.get_repeated_mistakes(session_id),
        "stats": voice_logger.get_session_stats(session_id),
    }


# ============================================================
# ENDPOINT 5: Audio — Emma Ki Awaaz Suno! 🎧
# ============================================================


@router.get("/audio/{filename}")
async def get_audio(filename: str):
    """
    GET /voice/audio/{filename}

    TTS se generated audio file serve karo.

    Yeh endpoint audio file ko stream karega browser ko.
    FileResponse automatically Content-Type set karta hai.

    Background cleanup:
    ───────────────────
    Audio serve hone ke baad delete karna chahiye (temp file hai).
    But abhi simple rakhte hain — cleanup_all() se baad mein karenge.
    """

    if not _tts_service:
        raise HTTPException(status_code=503, detail="TTS service not available")

    # TTS service ke temp directory mein dhundho
    import os

    audio_path = os.path.join(str(_tts_service.temp_dir), filename)

    if not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail="Audio file not found")

    return FileResponse(
        path=audio_path,
        media_type="audio/mpeg",
        filename=filename,
    )
