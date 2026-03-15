# 🎓 AI Teacher — Fully Local AI Teaching System

> **Learn English & Crack Coding Interviews — All running on YOUR laptop. No APIs. No cloud. No cost.**

[![Built with](https://img.shields.io/badge/LLM-phi3:mini-blue)]()
[![Built with](https://img.shields.io/badge/Vector_DB-ChromaDB-green)]()
[![Built with](https://img.shields.io/badge/Backend-FastAPI-teal)]()
[![Built with](https://img.shields.io/badge/Embeddings-Sentence_Transformers-orange)]()

---

## 🤔 What is this?

A **100% local AI teacher** with two modes:

| 🇬🇧 English Teacher | 💻 Coding Interview Tutor |
|---|---|
| Grammar correction | DSA question practice |
| Conversation practice | Step-by-step solutions |
| Vocabulary building | Hints before answers |
| Professional email writing | Time/Space complexity analysis |

**Everything runs locally** on a laptop with GTX 1650 + 16GB RAM. Zero API calls. Zero cost. Full privacy.

---

## 🏗️ Architecture

```
User Question
    → RAG Search (find relevant knowledge from ChromaDB)
    → LLM Answer (phi3:mini generates response with context)
    → Verification (same LLM double-checks the answer)
    → Response to User (with confidence score)
```

### Tech Stack

| Layer | Technology | Why |
|---|---|---|
| LLM | phi3:mini via Ollama | Small (4.4GB), runs on consumer GPUs |
| Vector DB | ChromaDB | Lightweight, persistent, no server needed |
| Embeddings | all-MiniLM-L6-v2 | 80MB, fast, good quality |
| Backend | Python FastAPI | Async, fast, auto-docs |
| Frontend | HTML/CSS/JS | No build tools, just open in browser |

---

## 📁 Project Structure

```
ai-teacher/
├── backend/
│   ├── app/
│   │   ├── config.py              # Centralized settings
│   │   ├── rag/retriever.py       # Semantic search in vector DB
│   │   ├── llm/ollama_client.py   # Communication with Ollama
│   │   ├── verification/verifier.py # Answer double-checking
│   │   ├── teachers/              # Teacher personalities (coming)
│   │   └── voice/                 # Whisper + Piper TTS (future)
│   ├── data/kb/                   # Knowledge base (JSON)
│   ├── chroma_db/                 # Vector database (auto-generated)
│   └── scripts/                   # Setup & utility scripts
├── frontend/                      # Chat UI (coming)
└── requirements.txt
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- [Ollama](https://ollama.com/) installed
- Git

### Setup

```bash
# 1. Clone the repo
git clone https://github.com/sagar-SgrDon/ai-teacher.git
cd ai-teacher

# 2. Create virtual environment
python -m venv venv
source venv/Scripts/activate   # Windows Git Bash
# OR: venv\Scripts\activate    # Windows CMD

# 3. Install dependencies
pip install -r requirements.txt

# 4. Pull the LLM model (one-time, ~4.4GB download)
ollama pull phi3:mini

# 5. Start Ollama server (keep running in separate terminal)
ollama serve

# 6. Test Ollama connection
python backend/scripts/test_ollama.py

# 7. Build vector database (one-time)
python backend/scripts/build_vectordb.py
```

---

## 📖 Learning Guide

This project is built step-by-step as a learning exercise. Each file has detailed comments explaining:
- **What** it does
- **Why** it's needed
- **How** it works (with real-world analogies)

### Build Order

| Step | File | Concept Learned |
|---|---|---|
| 1 | `scripts/test_ollama.py` | REST APIs, HTTP requests, JSON |
| 2 | `data/kb/*.json` | Knowledge base design, data structuring |
| 3 | `scripts/build_vectordb.py` | Embeddings, vector search, ChromaDB |
| 4 | `app/rag/retriever.py` | RAG pattern, semantic search |
| 5 | `app/llm/ollama_client.py` | Prompt engineering, LLM APIs |
| 6 | `app/verification/verifier.py` | Self-verification, confidence scoring |
| 7-8 | `app/main.py` + teachers | FastAPI, REST endpoints (coming) |
| 9 | `frontend/*` | HTML/CSS/JS, fetch API (coming) |
| 10 | `app/voice/*` | Speech-to-text, TTS (future) |

---

## 🔧 Hardware Requirements

| Component | Minimum | Recommended |
|---|---|---|
| GPU | GTX 1650 (4GB VRAM) | RTX 3060+ |
| RAM | 16GB | 16GB+ |
| Storage | ~6GB free | 10GB+ |
| CPU | Any modern quad-core | — |

---

## 📝 License

This project is built for learning purposes. Feel free to use, modify, and share.

---

*Built with ❤️ for learning AI engineering from scratch.*
