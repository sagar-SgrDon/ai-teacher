# 🎓 AI Teacher — System Design Document

> A fully local, privacy-first AI teaching system built for learning. No APIs. No cloud. Your laptop is the classroom.

| Spec           | Value                        |
| -------------- | ---------------------------- |
| **Python**     | 3.10 – 3.12 (⚠️ 3.13+ not supported) |
| **Hardware**   | GTX 1650 GPU, 16GB RAM       |
| **LLM**        | phi3:mini via Ollama (local) |
| **Vector DB**  | ChromaDB (local, persistent) |
| **Embeddings** | all-MiniLM-L6-v2 (384-dim)   |
| **Backend**    | Python FastAPI               |
| **Frontend**   | React + Vite + TypeScript    |
| **Styling**    | Tailwind CSS v4 + shadcn/ui  |
| **DevOps**     | Docker, GitHub Actions       |

---

## 1. System Architecture

```mermaid
graph TB
    subgraph Frontend["🖥️ Frontend (Browser)"]
        UI[Chat UI<br/>HTML/CSS/JS]
    end

    subgraph Backend["⚙️ Backend (FastAPI)"]
        API["/ask Endpoint"]
        ET[English Teacher]
        CT[Coding Teacher]
    end

    subgraph Core["🧠 Core Pipeline"]
        RAG[RAG Retriever]
        LLM[Ollama Client]
        VER[Answer Verifier]
    end

    subgraph Data["💾 Data Layer"]
        KB[Knowledge Base<br/>JSON Files]
        VDB[ChromaDB<br/>Vector Database]
        EMB[Sentence-Transformers<br/>Embedding Model]
    end

    subgraph Infra["🔧 Infrastructure"]
        OLL[Ollama Server<br/>localhost:11434]
        PHI[phi3:mini Model<br/>2.2 GB]
    end

    UI -->|HTTP POST /ask| API
    API --> ET & CT
    ET & CT --> RAG
    RAG --> VDB
    VDB --> EMB
    RAG -->|context| LLM
    LLM -->|answer| VER
    VER -->|verified answer| API
    API -->|JSON response| UI
    LLM --> OLL --> PHI
    KB -.->|build_vectordb.py| VDB
```

---

## 2. The Pipeline — How a Question Gets Answered

Every question flows through 5 stages:

```mermaid
sequenceDiagram
    actor User
    participant FE as Frontend
    participant API as FastAPI
    participant RAG as RAG Retriever
    participant LLM as Ollama (phi3:mini)
    participant VER as Verifier

    User->>FE: "How to solve Two Sum?"
    FE->>API: POST /ask {question, teacher_type: "coding"}

    Note over API: Stage 1: Route to correct teacher

    API->>RAG: search("Two Sum", collection="coding")
    Note over RAG: Stage 2: Semantic search in ChromaDB
    RAG-->>API: Top 3 relevant knowledge chunks

    API->>LLM: prompt = context + question
    Note over LLM: Stage 3: Generate answer with context
    LLM-->>API: "Use a hash map. For each number..."

    API->>VER: verify(question, answer, context)
    Note over VER: Stage 4: Self-verification (temp=0.3)
    VER-->>API: {is_verified: true, confidence: "high"}

    Note over API: Stage 5: Build final response
    API-->>FE: JSON {answer, confidence, sources}
    FE-->>User: Display answer with confidence badge
```

### Why this order matters

| Stage               | What                        | Why                                           | Without it                         |
| ------------------- | --------------------------- | --------------------------------------------- | ---------------------------------- |
| **1. Route**        | Pick English/Coding teacher | Different system prompts, different knowledge | Wrong personality, wrong data      |
| **2. RAG Search**   | Find relevant knowledge     | Give LLM factual reference material           | Hallucination — LLM makes stuff up |
| **3. LLM Generate** | Create answer with context  | Context = "open book exam" for the AI         | Unreliable answers                 |
| **4. Verify**       | Double-check the answer     | Catch obvious factual errors                  | Wrong info reaches the user        |
| **5. Respond**      | Send to user with metadata  | Confidence score helps user judge reliability | User blindly trusts everything     |

---

## 3. Component Deep Dive

### 3.1 RAG Retriever — `backend/app/rag/retriever.py`

**One-line:** Takes a question → finds the most relevant knowledge from ChromaDB.

```
User Question → Embedding Model (text → 384 numbers) → ChromaDB Search → Top 3 Results
```

**Key design decisions:**

| Decision             | Choice           | Rationale                                      |
| -------------------- | ---------------- | ---------------------------------------------- |
| Embedding model      | all-MiniLM-L6-v2 | Only 80MB, runs on CPU, good quality for size  |
| Vector dimensions    | 384              | Balance between accuracy and speed             |
| Top-K results        | 3                | Sweet spot — enough context without noise      |
| Separate collections | english / coding | Prevents cross-contamination of search results |

**Core methods:**

```python
# Search — returns ranked results with distance scores
results = retriever.search("How to reverse linked list?", teacher_type="coding")
# → [{"text": "...", "topic": "Reverse a Linked List", "distance": 0.61}, ...]

# Format — converts results into LLM-readable context
context = retriever.format_context(results)
# → "[Source 1] (Topic: Reverse a Linked List)\n..."
```

**What is "distance"?** Lower = better match. Think of it as GPS distance — 0.6 means very close (similar meaning), 1.5 means far (different topic).

---

### 3.2 Ollama Client — `backend/app/llm/ollama_client.py`

**One-line:** Sends prompts to phi3:mini through Ollama's local REST API, gets answers back.

```
[System Prompt + Prompt + Temperature] → Ollama API → phi3:mini → Answer Text
```

**Prompt Engineering — the most underrated skill:**

```
❌ BAD PROMPT:   "Two Sum bata"
✅ GOOD PROMPT:  System: "You are a coding tutor."
                 User: "Using this reference: [RAG context]
                        Explain Two Sum step by step"
```

**Temperature explained:**

```
🧊 0.0 ──── 0.3 ──── 0.5 ──── 0.7 ──── 1.0 🔥
   |          |         |         |         |
 Robotic   Verifier  Balanced  Teacher   Poet
 (exact)   (strict)            (our     (wild)
                                pick)
```

---

### 3.3 Answer Verifier — `backend/app/verification/verifier.py`

**One-line:** Takes LLM's answer → asks the same LLM "is this correct?" → returns confidence score.

```
LLM's Answer → Verification Prompt → Same LLM (temp=0.3) → Parse → Verdict
  CORRECT       → ✅ confidence: high
  PARTIALLY     → ⚠️ confidence: medium
  INCORRECT     → ❌ confidence: low + corrected answer
```

**Why temp=0.3 for verification?** Verification needs to be strict — no creativity. Like a math teacher grading papers.

> ⚠️ **Note:** Self-verification is NOT 100% reliable (same LLM checks itself). But it catches ~60-70% of obvious errors.

---

### 3.4 Teachers — `backend/app/teachers/`

**One-line:** Each teacher is a personality wrapper around the same RAG+LLM+Verifier pipeline.

| File                 | Class            | System Prompt                                              | Knowledge Collection |
| -------------------- | ---------------- | ---------------------------------------------------------- | -------------------- |
| `english_teacher.py` | `EnglishTeacher` | "Friendly English teacher, correct grammar, give examples" | `english_knowledge`  |
| `coding_teacher.py`  | `CodingTeacher`  | "Coding tutor, explain DSA, mention complexity"            | `coding_knowledge`   |

**Design Pattern — Duck Typing:**

```python
# Both teachers have the SAME method signature:
english_teacher.ask(question) → {answer, confidence, sources, ...}
coding_teacher.ask(question)  → {answer, confidence, sources, ...}

# So main.py doesn't care WHICH teacher — just call .ask()!
teacher = pick_teacher(teacher_type)  # could be either
result = teacher.ask(question)        # same interface!
```

---

### 3.5 FastAPI Application — `backend/app/main.py`

**One-line:** The entry point that receives HTTP requests, routes to the correct teacher, and returns JSON responses.

**Endpoints:**

| Method | Path      | Purpose                              | Request Body                       |
| ------ | --------- | ------------------------------------ | ---------------------------------- |
| `GET`  | `/health` | Check if server + Ollama are running | None                               |
| `POST` | `/ask`    | Ask a question to a teacher          | `{question, teacher_type, verify}` |

**Key concepts used:**

- **Pydantic BaseModel** — validates request/response format automatically
- **CORS Middleware** — allows frontend (different port) to talk to backend
- **Startup Event** — loads models once at server start, not per-request
- **HTTPException** — proper error responses with status codes

**Startup flow:**

```
Server starts → Load RAGRetriever (embedding model + ChromaDB)
             → Load OllamaClient (connect to Ollama)
             → Load AnswerVerifier (uses OllamaClient)
             → Create EnglishTeacher (gets all 3 components)
             → Create CodingTeacher (gets all 3 components)
             → Ready to serve requests!
```

---

## 4. Data Architecture

### Knowledge Base Stats

| Collection | Items | Categories                                                                                       |
| ---------- | ----- | ------------------------------------------------------------------------------------------------ |
| English    | 14    | Grammar (7), Vocabulary (3), Conversation (3), Writing (1)                                       |
| Coding     | 14    | Arrays (3), Strings (2), Linked List (2), Stack (1), Trees (2), DP (2), Search (1), Hash Map (1) |

### Coding Knowledge Item Schema

```json
{
  "id": "dsa_array_001",
  "topic": "Arrays - Two Sum",
  "category": "arrays",
  "difficulty": "easy",
  "question": "Given an array...",
  "hints": ["Hint 1", "Hint 2"],
  "solution": "def two_sum(nums, target): ...",
  "explanation": "We use a hash map...",
  "time_complexity": "O(n)",
  "space_complexity": "O(n)"
}
```

---

## 5. Project Structure

```
ai-teacher/
├── backend/
│   ├── app/
│   │   ├── config.py                 # All settings in one place
│   │   ├── main.py                   # FastAPI app — entry point
│   │   ├── rag/retriever.py          # Semantic search
│   │   ├── llm/ollama_client.py      # Talk to phi3:mini
│   │   ├── verification/verifier.py  # Double-check answers
│   │   ├── teachers/
│   │   │   ├── english_teacher.py    # English teacher personality
│   │   │   └── coding_teacher.py     # Coding teacher personality
│   │   ├── services/                 # Business logic (future)
│   │   └── voice/                    # Whisper + Piper TTS (future)
│   ├── data/kb/                      # Knowledge base JSONs
│   ├── chroma_db/                    # Vector database (auto-generated)
│   └── scripts/                      # Setup & utility scripts
├── frontend/                         # React + Vite + TypeScript
│   ├── src/
│   │   ├── main.tsx                  # React entry point
│   │   ├── App.tsx                   # Root component
│   │   ├── index.css                 # Global styles + Tailwind
│   │   ├── components/               # Reusable UI blocks
│   │   ├── pages/                    # Full pages (Chat, Topics)
│   │   └── services/                 # API communication layer
│   ├── package.json                  # Node dependencies
│   └── vite.config.ts                # Vite configuration
├── docs/                             # This documentation
├── docker-compose.yml                # Container orchestration
├── .github/workflows/                # CI/CD pipelines
├── requirements.txt
└── README.md
```

---

## 6. Complete Tech Stack

### Frontend

| Technology     | Version | Purpose                                           |
| -------------- | ------- | ------------------------------------------------- |
| React          | 19.x    | UI framework — component-based architecture       |
| Vite           | 7.x     | Build tool — blazing fast HMR, instant dev server |
| TypeScript     | 5.x     | Type safety — catch bugs at compile time          |
| Tailwind CSS   | v4      | Utility-first CSS — rapid UI development          |
| shadcn/ui      | latest  | Premium UI components — buttons, dialogs, cards   |
| Framer Motion  | 12.x    | Smooth animations — transitions, gestures         |
| Zustand        | 5.x     | State management — simple, fast, 10-line setup    |
| React Router   | v7      | Page routing — Topics page, Chat page             |
| Lucide React   | latest  | Icon library — 1500+ clean icons                  |
| Axios          | 1.x     | HTTP client — API calls with interceptors         |
| TanStack Query | v5      | Server state — caching, retries, loading states   |
| Vitest         | latest  | Unit testing — fast, Vite-native                  |

### Backend

| Technology                 | Purpose                            |
| -------------------------- | ---------------------------------- |
| Python 3.10–3.12           | ⚠️ 3.13+ breaks ChromaDB (Pydantic v1 incompatibility) |
| Python FastAPI             | REST API framework                 |
| Ollama + phi3:mini (2.2GB) | Local LLM inference                |
| ChromaDB                   | Vector database for RAG            |
| Sentence-Transformers      | Text embeddings (all-MiniLM-L6-v2) |
| Pydantic                   | Request/response validation        |
| Pytest                     | Backend unit testing               |

### DevOps & Infrastructure

| Technology          | Purpose                                           | Cost                  |
| ------------------- | ------------------------------------------------- | --------------------- |
| Docker + Compose    | Containerization — consistent env across machines | Free                  |
| GitHub Actions      | CI/CD — auto test + lint on every push            | Free (2000 min/month) |
| Husky + lint-staged | Pre-commit hooks — check code before commit       | Free                  |
| ESLint + Prettier   | Code quality + auto-formatting                    | Free                  |
| Vercel              | Frontend hosting (production)                     | Free tier             |
| Railway / Render    | Backend hosting (production)                      | Free tier             |

### Future Additions

| Technology        | Purpose             |
| ----------------- | ------------------- |
| React Three Fiber | 3D avatar rendering |
| Ready Player Me   | Avatar generator    |
| Whisper           | Speech-to-text      |
| Piper TTS         | Text-to-speech      |
| Rhubarb Lip Sync  | Avatar lip syncing  |

---

## 7. DevOps Pipeline

```
Developer pushes code
        ↓
Husky (pre-commit)
├── ESLint check (code quality)
├── Prettier format (code style)
└── Type check (TypeScript)
        ↓
GitHub Actions (CI)
├── Install dependencies
├── Run linter
├── Run frontend tests (Vitest)
├── Run backend tests (Pytest)
└── Build check (npm run build)
        ↓
Deploy (CD) — on main branch
├── Frontend → Vercel (auto-deploy)
└── Backend → Railway / Render
```

---

## 8. Design Patterns

| Pattern                    | Where                          | What it does                                |
| -------------------------- | ------------------------------ | ------------------------------------------- |
| **RAG**                    | Retriever + LLM                | Grounds LLM responses in factual data       |
| **Self-Verification**      | Verifier                       | Same LLM reviews its own answer             |
| **Dependency Injection**   | Verifier takes LLM client      | Swap LLM without changing verifier code     |
| **Duck Typing**            | EnglishTeacher / CodingTeacher | Same `.ask()` interface, different behavior |
| **Component Architecture** | React frontend                 | Reusable, isolated UI blocks                |
| **Single Source of Truth** | config.py, Zustand stores      | All settings/state in one place             |
| **Pipeline**               | RAG → LLM → Verify             | Each stage transforms data for the next     |
| **Separation of Concerns** | rag/ llm/ verification/        | Each module does ONE job well               |

---

## 9. Build Progress

| Phase             | Step                  | Status     | Tech                           |
| ----------------- | --------------------- | ---------- | ------------------------------ |
| **Foundation**    | 1. Ollama test        | ✅ Done    | `scripts/test_ollama.py`       |
|                   | 2. Knowledge Base     | ✅ Done    | `data/kb/*.json`               |
|                   | 3. Vector DB          | ✅ Done    | `scripts/build_vectordb.py`    |
| **Core Pipeline** | 4. RAG Retriever      | ✅ Done    | `app/rag/retriever.py`         |
|                   | 5. LLM Client         | ✅ Done    | `app/llm/ollama_client.py`     |
|                   | 6. Verifier           | ✅ Done    | `app/verification/verifier.py` |
| **API**           | 7. FastAPI            | ✅ Done    | `app/main.py`                  |
|                   | 8. Teachers           | ✅ Done    | `app/teachers/*.py`            |
| **Frontend**      | 9. React+Vite setup   | ✅ Done    | TypeScript template            |
|                   | 10. Tailwind + shadcn | ✅ Done    | Tailwind v4, shadcn Nova       |
|                   | 11. Chat UI           | ✅ Done    | Components + Zustand + API     |
|                   | 12. Topics UI         | 🔲 Planned | Udemy-style course view        |
| **DevOps**        | 13. Docker            | 🔲 Planned | Containerization               |
|                   | 14. GitHub Actions    | 🔲 Planned | CI/CD pipeline                 |
| **Voice**         | 15. Whisper+Piper     | 🔲 Future  | STT + TTS                      |
| **Avatar**        | 16. 3D Avatar         | 🔲 Future  | React Three Fiber              |

---

## 10. Performance Benchmarks

Tested on GTX 1650, 16GB RAM, phi3:mini (2.2GB):

| Operation                      | Time  | Notes                                   |
| ------------------------------ | ----- | --------------------------------------- |
| RAG Search                     | ~0.5s | Embedding model cached after first load |
| LLM Generation (no verify)     | ~30s  | Single inference pass                   |
| LLM Generation (with verify)   | ~60s  | Two inference passes                    |
| Server startup                 | ~10s  | Model loading + ChromaDB connection     |
| Embedding model first download | ~10s  | 80MB, cached after first run            |

---

## 11. Quick Reference Commands

```bash
# ── Backend ──
ollama serve                                          # Start LLM server
source venv/Scripts/activate                          # Activate Python env
python backend/scripts/build_vectordb.py              # Build vector DB
uvicorn backend.app.main:app --reload --port 8000     # Start API server

# ── Frontend ──
cd frontend && npm run dev                            # Start React dev server
npm run build                                         # Production build → dist/

# ── Test URLs ──
# Backend Health:  http://localhost:8000/health
# Backend Swagger: http://localhost:8000/docs
# Frontend:        http://localhost:5173
```

---

## 12. Bugs Found & Fixed

| Bug                                   | Where                                     | Fix                                     | Lesson                                       |
| ------------------------------------- | ----------------------------------------- | --------------------------------------- | -------------------------------------------- |
| `is_verified: true` when verify=false | `english_teacher.py`, `coding_teacher.py` | Changed default to `is_verified: False` | Default values must reflect actual state     |
| `coding_tutor` variable not found     | `main.py`                                 | Renamed to `coding_teacher`             | Always rename in ALL places when refactoring |

---

_This document is updated as the project progresses. Last updated: Step 11 — Chat UI complete, frontend-backend connected._
