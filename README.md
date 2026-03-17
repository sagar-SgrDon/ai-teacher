# 🎓 AI Teacher — Fully Local AI Teaching System

> **Learn English & Crack Coding Interviews — All running on YOUR laptop. No APIs. No cloud. No cost.**

[![LLM](https://img.shields.io/badge/LLM-phi3:mini_(2.2GB)-blue)]()
[![Vector DB](https://img.shields.io/badge/Vector_DB-ChromaDB-green)]()
[![Backend](https://img.shields.io/badge/Backend-FastAPI-teal)]()
[![Frontend](https://img.shields.io/badge/Frontend-React_+_Vite_+_TypeScript-61DAFB)]()
[![Styling](https://img.shields.io/badge/Styling-Tailwind_v4_+_shadcn/ui-38BDF8)]()

---

## 🤔 What is this?

A **100% local AI teacher** with two modes:

| 🇬🇧 English Teacher | 💻 Coding Interview Tutor |
|---|---|
| Grammar correction | DSA question practice |
| Conversation practice | Step-by-step solutions |
| Vocabulary building | Hints before answers |
| Professional email writing | Time/Space complexity analysis |

**Everything runs locally** — zero API calls, zero cost, full privacy.

---

## 🏗️ Architecture

```
User Question
    → RAG Search (find relevant knowledge from ChromaDB)
    → LLM Answer (phi3:mini generates response with context)
    → Verification (same LLM double-checks the answer)
    → Response to User (with confidence score + sources)
```

---

## 📋 Prerequisites — What You Need to Install

> 💡 Follow this order exactly. If you already have something installed, skip that step.

### 1. Git (Version Control)

**What:** Tracks code changes. Also needed to clone this repo.

| OS | Install |
|---|---|
| **Windows** | Download from [git-scm.com](https://git-scm.com/download/win) → Install → Use Git Bash |
| **Mac** | `brew install git` (or install Xcode Command Line Tools) |
| **Linux** | `sudo apt install git` (Ubuntu/Debian) |

**Verify:** `git --version` → should show version number

---

### 2. Python 3.10+

**What:** Backend language. All AI logic is in Python.

| OS | Install |
|---|---|
| **Windows** | Download from [python.org](https://www.python.org/downloads/) → ⚠️ **CHECK "Add Python to PATH"** during install! |
| **Mac** | `brew install python` |
| **Linux** | `sudo apt install python3 python3-venv python3-pip` |

**Verify:** `python --version` → should show 3.10 or higher

> ⚠️ **Windows users:** If `python` doesn't work, try `python3`. If neither works, Python is NOT in your PATH — reinstall and check "Add to PATH".

---

### 3. Node.js 18+ & npm

**What:** JavaScript runtime. Needed for the React frontend.

| OS | Install |
|---|---|
| **Windows** | Download LTS from [nodejs.org](https://nodejs.org/) → Install |
| **Mac** | `brew install node` |
| **Linux** | `sudo apt install nodejs npm` (or use [nvm](https://github.com/nvm-sh/nvm)) |

**Verify:**
```bash
node --version    # → v18 or higher
npm --version     # → should show version number
```

---

### 4. Ollama (Local LLM Server)

**What:** Runs AI models (like phi3:mini) locally on your GPU/CPU.

| OS | Install |
|---|---|
| **Windows** | Download from [ollama.com](https://ollama.com/) → Install |
| **Mac** | Download from [ollama.com](https://ollama.com/) or `brew install ollama` |
| **Linux** | `curl -fsSL https://ollama.ai/install.sh \| sh` |

**After installing — pull the AI model (one-time, ~2.2GB download):**
```bash
ollama pull phi3:mini
```

**Verify:** `ollama list` → should show `phi3:mini`

---

### 5. GPU Driver (Recommended, not required)

**What:** Ollama can run on CPU but it's 5-10x slower. GPU is highly recommended.

| GPU | Driver |
|---|---|
| **NVIDIA** | Download from [nvidia.com/drivers](https://www.nvidia.com/Download/index.aspx) |
| **AMD** | Download from [amd.com/support](https://www.amd.com/en/support) |
| **No GPU** | Ollama will auto-fallback to CPU (slower but works) |

**Verify (NVIDIA):** `nvidia-smi` → should show your GPU name and driver version

---

## 🚀 Setup — Getting the Project Running

### Step 1: Clone the Repository

```bash
git clone https://github.com/sagar-SgrDon/ai-teacher.git
cd ai-teacher
```

### Step 2: Backend Setup

```bash
# Create Python virtual environment
python -m venv venv

# Activate it
source venv/Scripts/activate     # Windows (Git Bash)
# OR
venv\Scripts\activate             # Windows (CMD / PowerShell)
# OR
source venv/bin/activate          # Mac / Linux

# Install Python dependencies
pip install -r requirements.txt
```

### Step 3: Build Vector Database (one-time)

```bash
python backend/scripts/build_vectordb.py
```

This loads the knowledge base, generates embeddings, and stores them in ChromaDB. Takes ~30 seconds on first run (~80MB model download).

### Step 4: Frontend Setup

```bash
cd frontend
npm install
cd ..
```

### Step 5: Start Everything (3 terminals needed)

**Terminal 1 — Ollama (LLM Server):**
```bash
ollama serve
```
> If you get "port already in use" error, Ollama is already running. That's fine!

**Terminal 2 — Backend (FastAPI):**
```bash
source venv/Scripts/activate     # Activate venv first
uvicorn backend.app.main:app --reload --port 8000
```
Wait for: `✅ AI Teacher Server ready!`

**Terminal 3 — Frontend (React):**
```bash
cd frontend
npm run dev
```
Wait for: `➜ Local: http://localhost:5173/`

### Step 6: Open in Browser 🎉

| URL | What |
|---|---|
| `http://localhost:5173` | **Chat UI** — Ask questions here! |
| `http://localhost:8000/docs` | **API Docs** — Swagger interactive API |
| `http://localhost:8000/health` | **Health Check** — Server status |

---

## 🛠️ Tech Stack

### Frontend
| Technology | Purpose |
|---|---|
| React 19 + Vite 7 + TypeScript | UI framework + build tool + type safety |
| Tailwind CSS v4 | Utility-first styling |
| shadcn/ui (Nova preset) | Premium UI components |
| Framer Motion | Smooth animations |
| Zustand | State management |
| Axios + TanStack Query | API communication |
| Lucide React | Icons |

### Backend
| Technology | Purpose |
|---|---|
| Python FastAPI | REST API framework |
| Ollama + phi3:mini (2.2GB) | Local LLM inference |
| ChromaDB | Vector database for RAG |
| Sentence-Transformers | Text embeddings (all-MiniLM-L6-v2) |
| Pydantic | Request/response validation |

### DevOps (Planned)
| Technology | Purpose |
|---|---|
| Docker + Compose | Containerization |
| GitHub Actions | CI/CD pipeline |

---

## 📁 Project Structure

```
ai-teacher/
├── backend/
│   ├── app/
│   │   ├── config.py                 # Centralized settings
│   │   ├── main.py                   # FastAPI entry point
│   │   ├── rag/retriever.py          # Semantic search in ChromaDB
│   │   ├── llm/ollama_client.py      # Communication with Ollama
│   │   ├── verification/verifier.py  # Answer double-checking
│   │   └── teachers/
│   │       ├── english_teacher.py    # English teacher personality
│   │       └── coding_teacher.py     # Coding teacher personality
│   ├── data/kb/                      # Knowledge base (JSON)
│   ├── chroma_db/                    # Vector DB (auto-generated)
│   └── scripts/                      # Setup & utility scripts
├── frontend/                         # React + Vite + TypeScript
│   └── src/
│       ├── components/               # UI components
│       ├── pages/                    # Page views
│       ├── services/                 # API layer
│       └── stores/                   # Zustand state
├── docs/                             # System design documentation
├── requirements.txt                  # Python dependencies
└── README.md                         # You are here!
```

---

## 📖 Learning Guide

Every file has detailed Hinglish comments explaining **what**, **why**, and **how** — with real-world analogies.

| Step | What You'll Learn |
|---|---|
| 1. `test_ollama.py` | REST APIs, HTTP requests, JSON |
| 2. `data/kb/*.json` | Knowledge base design, data structuring |
| 3. `build_vectordb.py` | Embeddings, vector search, ChromaDB |
| 4. `retriever.py` | RAG pattern, semantic search |
| 5. `ollama_client.py` | Prompt engineering, LLM APIs |
| 6. `verifier.py` | Self-verification, confidence scoring |
| 7. `main.py` | FastAPI, REST endpoints, Pydantic |
| 8. `teachers/*.py` | Duck typing, same interface different behavior |
| 9. React components | Components, state, hooks, TypeScript |

---

## ⚡ Performance

Tested on GTX 1650, 16GB RAM:

| Operation | Time |
|---|---|
| RAG Search | ~0.5s |
| LLM Response (no verify) | ~30-50s |
| LLM Response (with verify) | ~60-90s |
| Server startup | ~10s |

---

## 🔧 Hardware Requirements

| Component | Minimum | Recommended |
|---|---|---|
| GPU | GTX 1650 (4GB VRAM) | RTX 3060+ |
| RAM | 16GB | 16GB+ |
| Storage | ~6GB free | 10GB+ |
| CPU | Any modern quad-core | — |

---

## 🐛 Troubleshooting

| Problem | Solution |
|---|---|
| `ollama serve` → port already in use | Ollama is already running — ignore this error |
| `python` command not found | Use `python3` or reinstall Python with "Add to PATH" checked |
| `npm` command not found | Install Node.js from [nodejs.org](https://nodejs.org/) |
| Frontend can't connect to backend | Make sure backend is running on port 8000 |
| Very slow responses (>2 min) | Check if Ollama is using GPU: `ollama ps` |
| `ERESOLVE` npm errors | Delete `node_modules` + `package-lock.json`, then `npm install` |

---

## 📝 License

This project is built for learning purposes. Feel free to use, modify, and share.

---

*Built with ❤️ for learning AI engineering from scratch.*
