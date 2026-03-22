# 🎓 AI Teacher — AI Teaching System with Voice & Native Language Support

> **Learn English & Crack Coding Interviews with an AI teacher who speaks YOUR language — Hinglish, Hindi, or English.**

[![LLM](https://img.shields.io/badge/LLM-Groq_Llama_70B-blue)]()
[![Fallback](https://img.shields.io/badge/Fallback-Ollama_phi3:mini-gray)]()
[![TTS](https://img.shields.io/badge/TTS-edge--tts-orange)]()
[![Vector DB](https://img.shields.io/badge/Vector_DB-ChromaDB-green)]()
[![Backend](https://img.shields.io/badge/Backend-FastAPI-teal)]()
[![Frontend](https://img.shields.io/badge/Frontend-React_+_Vite_+_TypeScript-61DAFB)]()

---

## 🤔 What is this?

An AI teacher with **dual LLM support** (cloud + local) and two teaching modes:

| 🇬🇧 English Teacher         | 💻 Coding Interview Tutor      |
| -------------------------- | ------------------------------ |
| Grammar correction         | DSA question practice          |
| Conversation practice      | Step-by-step solutions         |
| Vocabulary building        | Hints before answers           |
| Professional email writing | Time/Space complexity analysis |

**Key features:**
- ☁️ **Groq cloud LLM** (default) — Llama 70B, blazing fast, excellent Hinglish
- 💻 **Ollama local** (fallback) — phi3:mini, works offline
- 🌐 **Native language support** — Emma teaches in Hinglish, Hindi, or English
- 🎧 **TTS** — Emma speaks! (Microsoft Neural Voices via edge-tts)
- 🎤 **STT** — Whisper speech-to-text (backend fallback)

---

## 🏗️ Architecture

```
User Question
    → RAG Search (find relevant knowledge from ChromaDB)
    → LLM Answer (Groq/Ollama generates response with context)
    → Verification (same LLM double-checks the answer)
    → TTS (edge-tts converts response to audio)
    → Response to User (text + audio + corrections)
```

---

## 📋 Prerequisites — What You Need to Install

> 💡 Follow this order exactly. If you already have something installed, skip that step.

### 1. Git (Version Control)

**What:** Tracks code changes. Also needed to clone this repo.

| OS          | Install                                                                                |
| ----------- | -------------------------------------------------------------------------------------- |
| **Windows** | Download from [git-scm.com](https://git-scm.com/download/win) → Install → Use Git Bash |
| **Mac**     | `brew install git` (or install Xcode Command Line Tools)                               |
| **Linux**   | `sudo apt install git` (Ubuntu/Debian)                                                 |

**Verify:** `git --version` → should show version number

---

### 2. Python 3.10 – 3.12

**What:** Backend language. All AI logic is in Python.

> ⚠️ **Python 3.13+ is NOT supported** — ChromaDB depends on Pydantic v1 which is incompatible with Python 3.13+. Use **Python 3.12** (recommended).

| OS          | Install                                                                                                                                                                     |
| ----------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Windows** | Download **3.12.x** from [python.org](https://www.python.org/downloads/release/python-31210/) → ⚠️ **CHECK "Add Python to PATH"** during install! Or run: `py install 3.12` |
| **Mac**     | `brew install python@3.12`                                                                                                                                                  |
| **Linux**   | `sudo apt install python3.12 python3.12-venv python3.12-dev`                                                                                                                |

**Verify:** `python --version` → should show 3.10, 3.11, or 3.12

> ⚠️ **Windows users:** If `python` doesn't work, try `py -3.12` or `python3`. If neither works, Python is NOT in your PATH — reinstall and check "Add to PATH".

---

### 3. Node.js 18+ & npm

**What:** JavaScript runtime. Needed for the React frontend.

| OS          | Install                                                                     |
| ----------- | --------------------------------------------------------------------------- |
| **Windows** | Download LTS from [nodejs.org](https://nodejs.org/) → Install               |
| **Mac**     | `brew install node`                                                         |
| **Linux**   | `sudo apt install nodejs npm` (or use [nvm](https://github.com/nvm-sh/nvm)) |

**Verify:**

```bash
node --version    # → v18 or higher
npm --version     # → should show version number
```

---

### 4. Ollama (Optional — only for offline/local mode)

**What:** Runs AI models locally on your GPU/CPU. Only needed if using `LLM_PROVIDER=ollama`.

| OS          | Install                                                                  |
| ----------- | ------------------------------------------------------------------------ |
| **Windows** | Download from [ollama.com](https://ollama.com/) → Install                |
| **Mac**     | Download from [ollama.com](https://ollama.com/) or `brew install ollama` |
| **Linux**   | `curl -fsSL https://ollama.ai/install.sh \| sh`                          |

**After installing (only if using Ollama):**

```bash
ollama pull phi3:mini
```

### 5. Groq API Key (Free — for cloud LLM, default)

**What:** Cloud LLM that’s 28x faster than local and speaks excellent Hinglish.

1. Go to [console.groq.com](https://console.groq.com) → Sign up (free)
2. Create an API Key
3. You'll paste this in `.env` file during setup

---

## 🚀 Setup — Getting the Project Running

### Step 1: Clone the Repository
```bash
git clone https://github.com/sagar-SgrDon/ai-teacher.git
cd ai-teacher
```
### Step 2: Backend Setup

```bash
# Create Python virtual environment (must use Python 3.10–3.12)
py -3.12 -m venv venv            # Windows (install 3.12 first if needed: py install 3.12)
# OR: python3.12 -m venv venv   # Mac / Linux

# Activate it
source venv/Scripts/activate     # Windows (Git Bash)
# OR
venv\Scripts\activate             # Windows (CMD / PowerShell)
# OR
source venv/bin/activate          # Mac / Linux

# Install Python dependencies
pip install -r requirements.txt
```

### Step 3: Environment Setup (🔑 API Keys)

```bash
# Copy the example env file
cp .env.example .env

# Edit .env and paste your Groq API key:
# GROQ_API_KEY=gsk_your_key_here
```

> 💡 Get your free Groq key at [console.groq.com](https://console.groq.com)

### Step 4: Build Vector Database (one-time)

```bash
python backend/scripts/build_vectordb.py
```

This loads the knowledge base, generates embeddings, and stores them in ChromaDB. Takes ~30 seconds on first run (~80MB model download).

### Step 5: Frontend Setup

```bash
cd frontend
npm install
cd ..
```

### Step 6: Start Everything (2 terminals)

**Terminal 1 — Backend (FastAPI):**

```bash
source venv/Scripts/activate     # Activate venv first
uvicorn backend.app.main:app --reload --port 8000
```

Wait for: `✅ AI Teacher Server ready!` and `☁️ Using Groq`

**Terminal 2 — Frontend (React):**

```bash
cd frontend
npm run dev
```

Wait for: `➜ Local: http://localhost:5173/`

### Step 7: Open in Browser 🎉

| URL                            | What                                   |
| ------------------------------ | -------------------------------------- |
| `http://localhost:5173`        | **Chat UI** — Ask questions here!      |
| `http://localhost:8000/docs`   | **API Docs** — Swagger interactive API |
| `http://localhost:8000/health` | **Health Check** — Server status       |

---

## 🛠️ Tech Stack

### Frontend

| Technology                     | Purpose                                 |
| ------------------------------ | --------------------------------------- |
| React 19 + Vite 7 + TypeScript | UI framework + build tool + type safety |
| Tailwind CSS v4                | Utility-first styling                   |
| shadcn/ui (Nova preset)        | Premium UI components                   |
| Framer Motion                  | Smooth animations                       |
| Zustand                        | State management                        |
| Axios + TanStack Query         | API communication                       |
| Lucide React                   | Icons                                   |

### Backend

| Technology                 | Purpose                            |
| -------------------------- | ---------------------------------- |
| Python FastAPI             | REST API framework                 |
| Groq API (Llama 3.3 70B)  | Cloud LLM — fast, excellent Hinglish (default) |
| Ollama + phi3:mini (2.2GB) | Local LLM — offline fallback       |
| edge-tts                   | Text-to-Speech (Microsoft Neural Voices) |
| openai-whisper             | Speech-to-Text (local, base.en)    |
| ChromaDB                   | Vector database for RAG            |
| Sentence-Transformers      | Text embeddings (all-MiniLM-L6-v2) |

---

## 📁 Project Structure

```
ai-teacher/
├── backend/
│   ├── app/
│   │   ├── config.py              # Centralized settings + dotenv
│   │   ├── main.py                # FastAPI entry point
│   │   ├── rag/retriever.py       # Semantic search in vector DB
│   │   ├── llm/
│   │   │   ├── ollama_client.py   # Local LLM + prompt builders
│   │   │   └── groq_client.py     # Cloud LLM (inherits OllamaClient)
│   │   ├── verification/verifier.py # Answer double-checking
│   │   ├── teachers/              # Teacher personalities
│   │   └── voice/                 # Voice conversation engine
│   │       ├── conversation_manager.py  # State machine + tracking
│   │       ├── voice_router.py      # API endpoints
│   │       ├── tts_service.py       # Text-to-Speech (edge-tts)
│   │       └── stt_service.py       # Speech-to-Text (Whisper)
│   ├── data/kb/                   # Knowledge base (JSON)
│   └── scripts/                   # Setup & utility scripts
├── frontend/                      # React + Vite + TypeScript
├── .env.example                   # Environment template (commit this)
├── .env                           # Your secrets (gitignored!)
└── requirements.txt
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10 – 3.12** (⚠️ Python 3.13+ NOT supported — ChromaDB/Pydantic v1)
- **Groq API key** (free at [console.groq.com](https://console.groq.com))
- Git

### Setup

```bash
# 1. Clone the repo
git clone https://github.com/sagar-SgrDon/ai-teacher.git
cd ai-teacher

# 2. Create virtual environment (use Python 3.12)
py -3.12 -m venv venv          # Windows
source venv/Scripts/activate   # Windows Git Bash

# 3. Install dependencies
pip install -r requirements.txt

# 4. Setup environment
cp .env.example .env
# Edit .env → paste your GROQ_API_KEY

# 5. Build vector database (one-time)
python backend/scripts/build_vectordb.py

# 6. Start server
uvicorn backend.app.main:app --reload --port 8000
```

---

## 📖 Learning Guide

Every file has detailed Hinglish comments explaining **what**, **why**, and **how** — with real-world analogies.

| Step                   | What You'll Learn                              |
| ---------------------- | ---------------------------------------------- |
| 1. `test_ollama.py`    | REST APIs, HTTP requests, JSON                 |
| 2. `data/kb/*.json`    | Knowledge base design, data structuring        |
| 3. `build_vectordb.py` | Embeddings, vector search, ChromaDB            |
| 4. `retriever.py`      | RAG pattern, semantic search                   |
| 5. `ollama_client.py`  | Prompt engineering, LLM APIs                   |
| 6. `verifier.py`       | Self-verification, confidence scoring          |
| 7. `main.py`           | FastAPI, REST endpoints, Pydantic              |
| 8. `teachers/*.py`     | Duck typing, same interface different behavior |
| 9. React components    | Components, state, hooks, TypeScript           |

---

## ⚡ Performance

Tested on GTX 1650, 16GB RAM:

| Operation               | Groq (Cloud) | Ollama (Local) |
| ----------------------- | ------------ | -------------- |
| Voice LLM (JSON mode)   | **~0.7s**    | ~15-20s        |
| TTS (edge-tts)          | ~5s          | ~5s            |
| Voice total (end-to-end)| **~6s**      | ~25-35s        |
| RAG Search              | ~0.5s        | ~0.5s          |

---

## 🔧 Hardware Requirements

| Component | Minimum              | Recommended |
| --------- | -------------------- | ----------- |
| GPU       | GTX 1650 (4GB VRAM)  | RTX 3060+   |
| RAM       | 16GB                 | 16GB+       |
| Storage   | ~6GB free            | 10GB+       |
| CPU       | Any modern quad-core | —           |

---

## 🐛 Troubleshooting

| Problem                              | Solution                                                                            |
| ------------------------------------ | ----------------------------------------------------------------------------------- |
| `GROQ_API_KEY` not set               | Edit `.env` file and paste your key from [console.groq.com](https://console.groq.com) |
| `ollama serve` → port already in use | Ollama is already running — ignore this error                                       |
| `python` command not found           | Use `py -3.12` or `python3` or reinstall Python with "Add to PATH" checked          |
| ChromaDB Pydantic error on startup   | You're on Python 3.13+. Recreate venv with 3.12: `py -3.12 -m venv venv`            |
| ChromaDB `PanicException` on startup | Delete `backend/chroma_db/` and rebuild: `python backend/scripts/build_vectordb.py` |
| `npm` command not found              | Install Node.js from [nodejs.org](https://nodejs.org/)                              |
| Frontend can't connect to backend    | Make sure backend is running on port 8000                                           |
| Very slow responses (>10 sec)        | Switch to Groq (set `LLM_PROVIDER=groq` in `.env`)                                 |
| Emma speaks in English not Hinglish  | Use Groq, not Ollama — phi3:mini can't do Hinglish well                             |

---

## 📝 License

This project is built for learning purposes. Feel free to use, modify, and share.

---

_Built with ❤️ for learning AI engineering from scratch._
