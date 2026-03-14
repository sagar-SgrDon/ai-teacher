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
