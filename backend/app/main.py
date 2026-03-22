"""
============================================================
STEP 7: FastAPI Application — Sab Ko Jodo!
============================================================

📖 EXPLANATION:

Yeh file poore system ka "MAIN GATE" hai.
Jab frontend question bhejta hai, yeh file woh request receive karti hai,
sahi teacher ko bhejti hai, aur jawab wapas karti hai.

FastAPI kya hai?
────────────────
Python ka ek framework jo HTTP API banane mein help karta hai.
Flask jaisa hai but MODERN aur FAST hai.

Kaise kaam karta hai?
1. Tum ek function likhte ho: def ask_question()
2. Uske upar decorator lagate ho: @app.post("/ask")
3. Ab jab koi /ask pe POST request bhejega → yeh function chalega!

DECORATOR kya hai? (@app.post)
─────────────────────────────
@ waala symbol ek "decorator" hai.
Socho jaise gift pe ribbon lagaate ho — gift wahi hai,
but ribbon lagane se woh special ban jaata hai.

@app.post("/ask") ka matlab:
"is function ko /ask URL pe POST requests ke liye register karo"

CORS kya hai?
─────────────
Cross-Origin Resource Sharing.
By default, browser BLOCK karta hai agar frontend (localhost:5500)
backend (localhost:8000) se baat kare — security ke liye.
CORS enable karne se browser allow karta hai yeh communication.
Socho jaise school mein pass chahiye doosre class mein jaane ke liye.

STARTUP EVENT kya hai?
──────────────────────
@app.on_event("startup") → server start hote hi yeh code chale.
Hum yahan model aur database load karte hain —
taaki pehli request pe delay na ho.
Socho jaise restaurant subah khulne se pehle kitchen ready karta hai.
============================================================
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json

# Apne modules import karo
from .rag.retriever import RAGRetriever
from .llm.ollama_client import OllamaClient
from .llm.groq_client import GroqClient
from .verification.verifier import AnswerVerifier
from .teachers.english_teacher import EnglishTeacher
from .teachers.coding_teacher import CodingTeacher
from .voice.voice_router import router as voice_router, init_voice_components
from .voice.tts_service import TTSService
from .config import LLM_PROVIDER


# ============================================================
# FastAPI App banao
# ============================================================

app = FastAPI(
    title="AI Teacher API",
    description="Local AI Teacher — English + Coding Interview Tutor",
    version="1.0.0",
)

# ---- CORS Setup ----
# Frontend (browser) se requests allow karo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # "*" = sabko allow karo (dev ke liye)
    # Production mein specific domain rakhna
    allow_credentials=True,
    allow_methods=["*"],  # GET, POST, PUT, DELETE — sab allow
    allow_headers=["*"],  # Sabhi headers allow
)


# ============================================================
# REQUEST / RESPONSE MODELS (Pydantic)
# ============================================================
# Pydantic models — yeh define karte hain ki request/response
# ka FORMAT kya hoga. FastAPI automatically validate karega.
#
# BaseModel kya hai?
# ──────────────────
# Pydantic ka BaseModel ek "form" jaisa hai.
# Tum define karo ki form mein kya fields chahiye,
# aur Pydantic check karega ki user ne sahi data bheja ya nahi.
# Galat data bheja → automatic error message!


class QuestionRequest(BaseModel):
    """Frontend se yeh data aayega."""

    question: str  # Student ka sawaal (required)
    teacher_type: str = "english"  # "english" ya "coding" (default: english)
    verify: bool = True  # Verification karna hai? (default: haan)


class AnswerResponse(BaseModel):
    """Frontend ko yeh data bhejenge."""

    answer: str  # Final jawab
    confidence: str  # "high" / "medium" / "low"
    is_verified: bool  # Verified hai ya nahi
    sources: list  # Kaunse topics se info aayi
    teacher: str  # Kaunsa teacher tha


# ============================================================
# GLOBAL VARIABLES — Components store karo
# ============================================================
# Yeh variables server start hone pe set honge (startup event mein)
# Global isliye hain kyunki har request mein same components chahiye
# Har request pe naya model load karna = SLOW aur WASTEFUL

retriever = None
llm_client = None
verifier = None
english_teacher = None
coding_teacher = None


# ============================================================
# STARTUP EVENT — Server start hote hi sab ready karo
# ============================================================


@app.on_event("startup")
async def startup():
    """
    Server start hote hi yeh chalega.

    async kya hai?
    ──────────────
    "async" ka matlab — yeh function "await" kar sakta hai.
    Abhi humne kuch await nahi kiya, but FastAPI ko async chahiye
    startup events ke liye. Aage jab database calls aayenge
    tab async ka asli fayda dikhega.

    Abhi ke liye bas samjho: async = "yeh function thoda
    special hai, wait kar sakta hai bina system ko block kiye"
    """

    # global keyword — "mujhe andar nahi, BAHAR waale variable ko change karna hai"
    # Bina global ke, Python sochega tum naya local variable bana rahe ho
    global retriever, llm_client, verifier, english_teacher, coding_teacher

    print("\n🎓 AI Teacher Server starting up...")
    print("=" * 50)

    # Step 1: Core components load karo
    print("\n📦 Loading components...")
    retriever = RAGRetriever()

    # LLM client choose karo — Groq (cloud) ya Ollama (local)
    if LLM_PROVIDER == "groq" and GroqClient.is_available():
        print("   ☁️ Using Groq (cloud LLM — better Hinglish!)")
        llm_client = GroqClient()
    else:
        print("   💻 Using Ollama (local LLM)")
        llm_client = OllamaClient()

    verifier = AnswerVerifier(llm_client)

    # Step 2: Teachers banao — inhe retriever, llm, verifier do
    print("\n👨‍🏫 Creating teachers...")
    english_teacher = EnglishTeacher(retriever, llm_client, verifier)
    coding_teacher = CodingTeacher(retriever, llm_client, verifier)

    # Step 3: Voice components connect karo
    print("\n🎤 Setting up voice module...")
    tts_service = TTSService()
    init_voice_components(retriever, llm_client, tts_service)
    app.include_router(voice_router, prefix="/voice")

    print("\n✅ AI Teacher Server ready!")
    print("=" * 50)


# ============================================================
# ENDPOINTS — API ke darwaaze
# ============================================================


@app.get("/health")
async def health_check():
    """
    Health check — server aur Ollama dono chal rahe hain ya nahi?

    GET /health — koi data nahi bhejte, sirf status poochte hain

    Yeh endpoint production mein bahut important hai.
    Monitoring tools isse har 30 second call karte hain —
    agar fail ho toh server restart karte hain.
    """

    ollama_ok = llm_client.is_available() if llm_client else False

    return {
        "status": "healthy" if ollama_ok else "unhealthy",
        "ollama": "connected" if ollama_ok else "disconnected",
        "teachers": ["english", "coding"],
    }


@app.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    """
    MAIN ENDPOINT — Yahan question aata hai, yahan se jawab jaata hai!

    POST /ask — question data BHEJTE hain

    request: QuestionRequest — FastAPI automatically JSON ko
    QuestionRequest object mein badal dega. Agar galat format
    mein data aaya toh 422 error dega (validation fail).

    response_model=AnswerResponse — FastAPI ko batata hai ki
    response ka format kya hoga. Auto documentation mein dikhta hai.

    HTTPException kya hai?
    ──────────────────────
    Jab kuch galat ho toh "error" response bhejo proper format mein.
    HTTP status codes:
      200 = sab sahi ✅
      400 = user ne galat data bheja ❌
      500 = server mein problem ❌
      422 = validation fail (auto by FastAPI) ❌
    """

    # ---- Step 1: Sahi teacher chuno ----
    if request.teacher_type == "english":
        teacher = english_teacher
    elif request.teacher_type == "coding":
        teacher = coding_teacher
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown teacher type: '{request.teacher_type}'. Use 'english' or 'coding'.",
        )

    if teacher is None:
        raise HTTPException(
            status_code=500, detail="Server abhi ready nahi hai. Thoda wait karo."
        )

    # ---- Step 2: Teacher se poocho ----
    try:
        print(f"\n📩 Question: {request.question}")
        print(f"   Teacher: {request.teacher_type}")

        result = teacher.ask(question=request.question, verify=request.verify)

        print(f"   ✅ Answer ready! Confidence: {result['confidence']}")

        return AnswerResponse(
            answer=result["answer"],
            confidence=result["confidence"],
            is_verified=result["is_verified"],
            sources=result["sources"],
            teacher=result["teacher"],
        )

    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Kuch galat ho gaya: {str(e)}")


# ============================================================
# STREAMING ENDPOINT — ChatGPT jaisa live response!
# ============================================================


@app.post("/ask/stream")
async def ask_question_stream(request: QuestionRequest):
    """
    Streaming version of /ask — response word by word aata hai!

    StreamingResponse kya hai?
    ─────────────────────────
    Normal response: Poora data ready karo → phir bhejo
    Streaming response: Thoda thoda data bhejte jao → client dikhata jaye

    SSE (Server-Sent Events) kya hai?
    ─────────────────────────────────
    Ek technique jismein server client ko CONTINUOUSLY data bhejta raha.
    Client ek baar connect karta hai, phir server jab chahe data push kare.

    ChatGPT, Claude, Gemini — sab SSE use karte hain streaming ke liye!

    "text/event-stream" = browser ko batao "yeh ek SSE connection hai"
    """

    # Teacher chuno
    if request.teacher_type == "english":
        teacher = english_teacher
    elif request.teacher_type == "coding":
        teacher = coding_teacher
    else:
        raise HTTPException(
            status_code=400, detail=f"Unknown teacher type: '{request.teacher_type}'"
        )

    if teacher is None:
        raise HTTPException(status_code=500, detail="Server abhi ready nahi hai.")

    # ---- Streaming generator function ----
    async def stream_response():
        """
        Yeh function yield karta hai — har token ke liye ek SSE event.

        SSE format:
        data: {"token": "Hello"}\n\n  ← ek event
        data: {"token": " world"}\n\n  ← doosra event
        data: [DONE]\n\n               ← signal: khatam!
        """

        # Step 1: RAG search (non-streaming — fast hai)
        search_results = teacher.rag.search(
            request.question, teacher_type=teacher.teacher_type
        )
        context = teacher.rag.format_context(search_results)
        sources = [r["topic"] for r in search_results]

        # Step 2: Prompt banao
        prompt, system_prompt = teacher.llm.build_rag_prompt(
            question=request.question,
            context=context,
            teacher_type=teacher.teacher_type,
        )

        # Step 3: Metadata pehle bhejo (sources, teacher info)
        meta = {
            "type": "meta",
            "sources": sources,
            "teacher": f"{'English Teacher 🇬🇧' if request.teacher_type == 'english' else 'Coding Teacher 💻'}",
        }
        yield f"data: {json.dumps(meta)}\n\n"

        # Step 4: Tokens stream karo — word by word!
        full_answer = ""
        for token in teacher.llm.generate_stream(
            prompt=prompt, system_prompt=system_prompt
        ):
            full_answer += token
            yield f"data: {json.dumps({'type': 'token', 'token': token})}\n\n"

        # Step 5: Verification (optional — streaming ke baad)
        confidence = "unverified"
        is_verified = False

        if request.verify:
            verification = teacher.verifier.verify(
                question=request.question, answer=full_answer, context=context
            )
            confidence = verification.get("confidence", "unverified")
            is_verified = verification.get("is_verified", False)

            # Agar verified answer alag hai toh bhejo
            verified_answer = verification.get("verified_answer", "")
            if verified_answer and verified_answer != full_answer:
                yield f"data: {json.dumps({'type': 'replace', 'text': verified_answer})}\n\n"

        # Step 6: Final metadata bhejo
        done = {
            "type": "done",
            "confidence": confidence,
            "is_verified": is_verified,
        }
        yield f"data: {json.dumps(done)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        stream_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
