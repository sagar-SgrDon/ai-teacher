"""
============================================================
STEP 8b: Coding Interview Teacher — DSA Sikhane Waala
============================================================

📖 EXPLANATION:

Yeh Coding Teacher ka personality card hai.
English teacher se structure SAME hai — but behavior alag:

1. DSA questions poocho → hints do → solution samjhao
2. Student ka code evaluate karo
3. Time/Space complexity explain karo

IMPORTANT PATTERN — "Same Interface, Different Behavior":
─────────────────────────────────────────────────────────
EnglishTeacher.ask(question) → {answer, confidence, ...}
CodingTeacher.ask(question)    → {answer, confidence, ...}

Dono ka OUTPUT format SAME hai!
Isliye main.py ko sirf itna pata hona chahiye:
  teacher = pick_teacher(teacher_type)
  result = teacher.ask(question)  ← same method, koi bhi teacher ho
============================================================
"""


class CodingTeacher:
    """
    Coding interview tutor ki personality.
    
    English teacher se SAME structure hai (ask method),
    but yeh DSA questions handle karta hai differently.
    """
    
    def __init__(self, rag_retriever, llm_client, verifier):
        """Same pattern as EnglishTeacher — tools store karo."""
        self.rag = rag_retriever
        self.llm = llm_client
        self.verifier = verifier
        self.teacher_type = "coding"
    
    def ask(self, question: str, verify: bool = True) -> dict:
        """
        Student ne coding question poocha — poora pipeline chalao.
        
        EnglishTeacher.ask() se bilkul SAME structure.
        Sirf teacher_type alag hai — "coding" instead of "english".
        
        Yeh "coding" teacher_type se teen cheezein badalti hain:
        1. RAG search mein "coding_knowledge" collection search hogi
        2. System prompt mein "You are a coding tutor" aayega
        3. Knowledge base mein DSA problems se match hoga
        """
        
        # ---- Step 1: RAG Search ----
        search_results = self.rag.search(question, teacher_type=self.teacher_type)
        context = self.rag.format_context(search_results)
        
        # ---- Step 2: LLM se jawab lo ----
        prompt, system_prompt = self.llm.build_rag_prompt(
            question=question,
            context=context,
            teacher_type=self.teacher_type
        )
        answer = self.llm.generate(prompt=prompt, system_prompt=system_prompt)
        
        # ---- Step 3: Verify ----
        verification = {"is_verified": False, "confidence": "unverified"}
        
        if verify:
            verification = self.verifier.verify(
                question=question,
                answer=answer,
                context=context
            )
        
        # ---- Step 4: Response banao ----
        sources = [r["topic"] for r in search_results]
        
        return {
            "answer": verification.get("verified_answer", answer),
            "original_answer": answer,
            "confidence": verification.get("confidence", "unverified"),
            "is_verified": verification.get("is_verified", False),
            "sources": sources,
            "teacher": "Coding Teacher 💻"
        }
