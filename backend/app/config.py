"""
============================================================
CONFIG: Saari Settings Ek Jagah
============================================================

📖 EXPLANATION:

Socho tumhare ghar mein ek "settings register" hai jahan sab
important cheezein likhi hain — Ollama ka address, model ka naam,
database ka path, etc.

Agar yeh sab ALAG-ALAG files mein hoti, toh agar address badalna
ho toh har file mein jaake change karna padta. Mushkil!

Isliye hum SAB settings ek hi jagah rakhte hain.
Isko kehte hain "Single Source of Truth" pattern.

🔧 CONCEPT: Configuration Management
- Settings ek jagah rakho → easy to change
- os.environ.get() = environment variable se padho, nahi mile toh default use karo
============================================================
"""

import os
from dotenv import load_dotenv

# .env file se environment variables load karo
# Yeh file project root mein hoti hai (ai-teacher/.env)
# Secrets (API keys etc.) .env mein rakhte hain, code mein NAHI!
load_dotenv()

# ============================================================
# PATHS
# ============================================================
# __file__ se is file ka location milta hai
# Phir wahan se project ke baaki folders ka path calculate karte hain

# Is file ka folder: backend/app/
APP_DIR = os.path.dirname(os.path.abspath(__file__))
# backend/ folder
BACKEND_DIR = os.path.dirname(APP_DIR)
# Project root: ai-teacher/
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)

# ChromaDB ka data yahan stored hai (Step 3 mein banaya tha)
CHROMA_DB_PATH = os.path.join(BACKEND_DIR, "chroma_db")

# Knowledge base files ka folder
KB_DATA_PATH = os.path.join(BACKEND_DIR, "data", "kb")

# ============================================================
# OLLAMA SETTINGS
# ============================================================
# Ollama ka address — default localhost pe chalta hai
# os.environ.get() ka matlab: pehle environment variable check karo
# agar nahi mila toh default value use karo
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")

# Kaunsa model use karna hai
# Tum "phi3:mini" use kar rahe ho — chhota aur fast hai
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "phi3:mini")

# ============================================================
# EMBEDDING SETTINGS
# ============================================================
# Wahi model jo Step 3 mein use kiya tha
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# ============================================================
# RAG SETTINGS
# ============================================================
# Search mein kitne results laane hain
# 3 is a sweet spot: zyada = slow + noisy, kam = miss ho sakta hai
RAG_TOP_K = 3

# ============================================================
# TEACHER TYPES
# ============================================================
# Yeh define karta hai ki kaunse teachers available hain
TEACHER_TYPES = ["english", "coding"]

# ============================================================
# LLM PROVIDER SETTINGS
# ============================================================
# LLM_PROVIDER decides kaunsa LLM use karna hai:
#   "groq"   → Cloud API (fast, better Hinglish, needs internet)
#   "ollama" → Local model (offline, but limited Hinglish)

LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "groq")  # Default: groq

# ============================================================
# GROQ SETTINGS (Cloud LLM — Better Hinglish!)
# ============================================================
# Groq = Free cloud API for LLMs (Llama 70B, Gemma, etc.)
# Signup: https://console.groq.com (30 req/min free!)
#
# LPU (Language Processing Unit) = Groq ka custom hardware
# Isliye itna fast hai — 2-5 seconds mein response!

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")  # API key from .env file
GROQ_MODEL = os.environ.get(
    "GROQ_MODEL", "llama-3.3-70b-versatile"
)  # Free, best for Hinglish
GROQ_FALLBACK_MODEL = os.environ.get(
    "GROQ_FALLBACK_MODEL", "llama-3.1-8b-instant"
)  # Fallback: 14.4K RPD (14x more daily requests!)
