"""
============================================================
STEP 5: Ollama Client — LLM se Baat Karo
============================================================

🎯 GOAL: RAG se mila hua context + User ka question → phi3:mini ko bhejo → jawab lo

📖 EXPLANATION (Hinglish mein):

Step 4 mein humne relevant info dhundh li (RAG Retriever se).
Ab woh info LLM ko deni hai taaki woh SAHI jawab de.

Bina context ke:
  User: "Two Sum kaise solve karein?"
  LLM: *apni memory se* → galat ho sakta hai

Context ke saath:
  User: "Two Sum kaise solve karein?"
  Context: "Two Sum: Use hash map, check complement exists..."
  LLM: *context pad ke* → SAHI jawab dega!

Yeh EXACTLY wahi hai jaise exam mein open book milti hai.
LLM ko hum "book" (context) de rahe hain padh ke likhne ke liye.

FLOW:
  context + question → prompt banao → Ollama API → jawab

🔧 CONCEPTS:
1. Prompt Engineering — LLM ko KAISE puchna hai (format matters!)
2. System Prompt — LLM ko uska "role" batana (tu teacher hai)
3. REST API — Ollama se HTTP ke through baat karna
4. Temperature — kitna creative ya strict jawab chahiye
============================================================
"""

import requests
import json
from ..config import OLLAMA_BASE_URL, OLLAMA_MODEL


class OllamaClient:
    """
    Ollama se baat karne ka class.
    
    Ollama kya karta hai?
    ─────────────────────
    Ollama ek "wrapper" hai jo LLM models ko locally run karta hai.
    Matlab: ChatGPT jaisa model tumhare APNE laptop pe chalta hai.
    
    Ollama apne aap ek HTTP server start karta hai (port 11434 pe).
    Hum us server ko "chitthi" (HTTP request) bhejte hain question ke saath,
    aur woh jawab wapas bhejta hai.
    
    Yeh class us "chitthi bhejne" ka kaam simple bana deti hai.
    """
    
    def __init__(self):
        """Constructor — Ollama ka address store karo."""
        
        self.base_url = OLLAMA_BASE_URL
        self.model = OLLAMA_MODEL
        
        print(f"✅ Ollama Client ready! (Model: {self.model})")
    
    def generate(self, prompt: str, system_prompt: str = None, temperature: float = 0.7) -> str:
        """
        LLM se jawab lo.
        
        Parameters:
        ──────────
        prompt        : Actual question/instruction (user ka sawaal + RAG context)
        system_prompt : LLM ka "role" define karta hai
                        Jaise: "You are an English teacher" ya "You are a coding tutor"
                        Yeh LLM ko batata hai ki woh KAUN hai aur KAISE jawab de
        temperature   : 0.0 = strict/factual, 1.0 = creative/random
                        Teacher ke liye 0.7 sahi hai — thoda creative but mostly accurate
        
        Returns:
        ────────
        str: LLM ka jawab (text)
        
        TEMPERATURE ko samjho:
        ─────────────────────
        Socho temperature ek dial hai:
        🧊 0.0 = Bahut strict. Hamesha SAME jawab dega. Maths ke liye accha.
        🌡️ 0.5 = Balance. Mostly same but thoda variation.
        🔥 1.0 = Bahut creative. Har baar ALAG jawab. Poetry ke liye accha.
        
        Hum 0.7 use kar rahe hain = thoda creative teacher jaisa
        """
        
        # ---- Step 1: Request body banao ----
        # Yeh woh "chitthi" hai jo Ollama ko bhejenge
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,         # Poora jawab ek baar mein (streaming nahi)
            "options": {
                "temperature": temperature,
                "num_predict": 1024,  # Maximum kitne words generate kare
                                      # 1024 tokens ≈ 750 words (roughly)
            }
        }
        
        # Agar system prompt diya hai toh add karo
        # System prompt = LLM ka "character card"
        if system_prompt:
            payload["system"] = system_prompt
        
        # ---- Step 2: Ollama ko request bhejo ----
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=120  # 2 minute max wait (phi3:mini thoda slow ho sakta hai)
            )
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get("response", "").strip()
                
                # Debug info (optional — production mein hata dena)
                duration = data.get("total_duration", 0) / 1_000_000_000
                print(f"   ⏱️ LLM response time: {duration:.1f}s")
                
                return answer
            else:
                error_msg = f"Ollama error! Status: {response.status_code}"
                print(f"❌ {error_msg}")
                return f"Error: {error_msg}"
                
        except requests.ConnectionError:
            error_msg = "Ollama se connect nahi ho pa raha! Kya 'ollama serve' chal raha hai?"
            print(f"❌ {error_msg}")
            return f"Error: {error_msg}"
            
        except requests.Timeout:
            error_msg = "Ollama ne bahut zyada time le liya (timeout 120s)"
            print(f"❌ {error_msg}")
            return f"Error: {error_msg}"
    
    def build_rag_prompt(self, question: str, context: str, teacher_type: str = "english") -> tuple:
        """
        RAG context + User question ko ek acche prompt mein badlo.
        
        Returns:
        ────────
        tuple: (prompt, system_prompt)
        
        TUPLE kya hai?
        ──────────────
        Tuple ek "packet" hai jismein multiple cheezein hoti hain.
        Jaise: (name, age) = ("Rahul", 25)
        List jaisa hai, but BADAL nahi sakte (immutable).
        
        PROMPT ENGINEERING kya hai?
        ───────────────────────────
        LLM se accha jawab lene ke liye ACCHA question poochna zaroori hai.
        
        Galat tarika: "Two Sum bata"
        Sahi tarika: "You are a coding tutor. Using the following reference 
                      material, explain the Two Sum problem step by step..."
        
        Format matters! Jaise exam mein question properly padhna zaroori hai,
        waise hi LLM ko properly poochna zaroori hai.
        """
        
        if teacher_type == "english":
            system_prompt = (
                "You are a friendly and patient English language teacher. "
                "You help students improve their grammar, vocabulary, and conversation skills. "
                "Use simple language. Give examples. "
                "If the student makes a grammar mistake, gently correct them and explain why. "
                "Be encouraging and supportive."
            )
        else:  # coding
            system_prompt = (
                "You are an experienced coding interview tutor. "
                "You help students understand Data Structures and Algorithms (DSA). "
                "Explain concepts step by step with examples. "
                "When presenting solutions, explain the logic before showing code. "
                "Always mention time and space complexity. "
                "Be encouraging — coding is hard but practice makes perfect!"
            )
        
        # RAG prompt = context + question
        prompt = f"""Use the following reference material to answer the student's question.
            If the reference material is relevant, base your answer on it.
            If it's not relevant, use your own knowledge but mention that it's from your general knowledge.

            --- REFERENCE MATERIAL ---
            {context}
            --- END REFERENCE ---

            Student's Question: {question}

            Please provide a clear, helpful, and accurate answer:"""
        
        return prompt, system_prompt
    
    def is_available(self) -> bool:
        """
        Quick check — Ollama chal raha hai ya nahi?
        
        Health check jaisa — doctor pehle check karta hai 
        "patient zinda hai?" phir treatment shuru karta hai 😄
        """
        try:
            response = requests.get(self.base_url, timeout=5)
            return response.status_code == 200
        except:
            return False
