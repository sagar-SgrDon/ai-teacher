"""
============================================================
STEP 8a: English Teacher — Angrezi Sikhane Waala
============================================================

📖 EXPLANATION:

Yeh file English teacher ka "personality card" hai.
Jaise har teacher ka apna style hota hai — yeh define karta hai
ki English teacher KAISE jawab dega.

3 main kaam karta hai:
1. Grammar check — "I goes" → "I go" (galti pakdo, samjhao)
2. Conversation practice — baat-cheet mein help
3. Vocabulary building — naye words sikhaao

Yeh SIRF personality define karta hai.
Actual LLM aur RAG ka kaam underlying pipeline karta hai.
Teacher sirf "kya poochna hai" aur "kaise jawab dena hai" decide karta hai.
============================================================
"""


class EnglishTeacher:
    """
    English teacher ki personality aur behavior.
    
    Yeh class ek "wrapper" hai — andar se RAG + LLM + Verifier 
    use karta hai, but bahar se dekhne mein ek simple teacher hai 
    jisse tum question poocho aur jawab lo.
    """
    
    def __init__(self, rag_retriever, llm_client, verifier):
        """
        Constructor — teacher ko uske "tools" do.
        
        Socho naya teacher school mein aaya:
        - rag_retriever = uski textbook (knowledge dhundne ke liye)
        - llm_client = uska brain (jawab generate karne ke liye)
        - verifier = uska checker (jawab sahi hai ya nahi)
        """
        self.rag = rag_retriever
        self.llm = llm_client
        self.verifier = verifier
        self.teacher_type = "english"
    
    def ask(self, question: str, verify: bool = True) -> dict:
        """
        Student ne question poocha — poora pipeline chalao.
        
        FLOW:
        question → RAG search → LLM answer → verify → response
        
        Parameters:
            question: Student ka sawaal
            verify: Kya double-check karna hai? (default: haan)
        
        Returns:
            dict with: answer, confidence, sources, is_verified
        """
        
        # ---- Step 1: RAG Search ----
        # Pehle relevant knowledge dhundho
        # Jaise teacher pehle textbook mein topic dhundhta hai
        search_results = self.rag.search(question, teacher_type=self.teacher_type)
        context = self.rag.format_context(search_results)
        
        # ---- Step 2: LLM se jawab lo ----
        # Context + question = prompt banao, phir LLM se poocho
        prompt, system_prompt = self.llm.build_rag_prompt(
            question=question,
            context=context,
            teacher_type=self.teacher_type
        )
        answer = self.llm.generate(prompt=prompt, system_prompt=system_prompt)
        
        # ---- Step 3: Verify (optional) ----
        verification = {"is_verified": False, "confidence": "unverified"}
        
        if verify:
            verification = self.verifier.verify(
                question=question,
                answer=answer,
                context=context
            )
        
        # ---- Step 4: Response banao ----
        # Sources = kaunse topics se info aayi
        sources = [r["topic"] for r in search_results]
        
        return {
            "answer": verification.get("verified_answer", answer),
            "original_answer": answer,
            "confidence": verification.get("confidence", "unverified"),
            "is_verified": verification.get("is_verified", False),
            "sources": sources,
            "teacher": "English Teacher 🇬🇧"
        }
