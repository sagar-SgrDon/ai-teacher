"""
============================================================
STEP 6: Answer Verifier — Jawab Double-Check Karo
============================================================

🎯 GOAL: LLM ka jawab mila → WAHI LLM se double-check karwao → 
         Confidence score do

📖 EXPLANATION (Hinglish mein):

Socho tum exam mein answer likh chuke ho. Ab ek baar PHIR padhte ho
apna answer — "Sahi likha hai ya kuch galat hai?"

Yahi kaam yeh verifier karta hai:
1. LLM ne jawab diya
2. Verifier WAHI jawab LLM ko wapas dikhata hai aur puchta hai:
   "Yeh jawab sahi hai? Koi galti toh nahi?"
3. LLM review karke batata hai: "Haan sahi hai" ya "Nahi, yeh galat hai"

Isko kehte hain "Self-Verification" pattern.

Kyun zaroori hai?
  ❌ Bina verification: LLM kahega "Linked List mein O(1) mein search hota hai" (GALAT!)
  ✅ Verification ke saath: Verifier bolega "Ruko! Linked List mein O(n) hota hai!"

100% accurate nahi hai (kyunki wahi LLM check kar raha hai), but 
bahut saari obvious galtiyan pakad leta hai. 
Socho jaise apna khud ka homework check karna — sab nahi pakdoge, 
but badi galtiyan zaroor pakdoge!

🔧 CONCEPTS:
1. Self-Verification — LLM apna answer khud review kare
2. Confidence Score — kitna bharosa hai jawab pe (low/medium/high)
3. Pipeline Pattern — ek ke baad ek step (RAG → LLM → Verify)
============================================================
"""

from ..llm.ollama_client import OllamaClient


class AnswerVerifier:
    """
    LLM ke jawab ko verify (double-check) karne ka class.
    
    Dependency Injection kya hai?
    ─────────────────────────────
    Is class ko OllamaClient BAHAR se milta hai (constructor mein).
    Khud nahi banata. Kyun?
    
    Socho: Agar tumhe chai banana hai, toh tum doodh KHUD nahi banaoge —
    doodh bahar se laoge. Waise hi yeh class LLM client bahar se leta hai.
    
    Faayda: Agar kal ko Ollama ki jagah koi aur LLM use karna ho,
    toh sirf client badlo, verifier ka code change nahi karna padega!
    """
    
    def __init__(self, llm_client: OllamaClient):
        """
        Constructor — LLM client store karo.
        
        llm_client: OllamaClient  →  Type hint: yeh parameter OllamaClient 
                                      type ka hona chahiye
        """
        self.llm_client = llm_client
        print("✅ Answer Verifier ready!")
    
    def verify(self, question: str, answer: str, context: str = "") -> dict:
        """
        Jawab ko verify karo.
        
        Parameters:
        ──────────
        question : Original question jo user ne poocha tha
        answer   : LLM ne jo jawab diya
        context  : RAG se mila hua reference material
        
        Returns:
        ────────
        dict with:
          - "is_verified": True/False (sahi hai ya nahi)
          - "confidence": "high" / "medium" / "low"
          - "feedback": Kya galat hai (agar kuch galat hai)
          - "original_answer": Original jawab
          - "verified_answer": Corrected jawab (agar correction thi)
        
        DICT kya hai?
        ─────────────
        Dictionary ek "label-waala dabba" hai.
        Jaise: {"naam": "Rahul", "age": 25, "city": "Mumbai"}
        Har cheez ka ek naam (key) hai aur ek value hai.
        List mein position se access karte hain: list[0]
        Dict mein naam se access karte hain: dict["naam"]
        """
        
        # ---- Verification Prompt banao ----
        # LLM ko original question, diya gaya answer, aur reference context dikhao
        # Phir poochho: "Yeh sahi hai?"
        
        verification_prompt = f"""You are a fact-checker and answer verifier. 
            Your job is to review an answer and check if it is correct and accurate.

            ORIGINAL QUESTION: {question}

            ANSWER TO VERIFY:
            {answer}

            REFERENCE MATERIAL (use this to check accuracy):
            {context if context else "No reference material available."}

            Please analyze the answer and respond in this EXACT format:
            VERDICT: CORRECT or INCORRECT or PARTIALLY_CORRECT
            CONFIDENCE: HIGH or MEDIUM or LOW
            ISSUES: List any issues found, or "None" if answer is correct
            CORRECTED_ANSWER: If there are issues, provide the corrected version. If correct, write "No correction needed."
            """
        
        # System prompt — verifier ka role define karo
        system_prompt = (
            "You are a strict but fair answer verifier. "
            "Check answers for factual accuracy, completeness, and clarity. "
            "Be concise in your feedback. "
            "Only mark as INCORRECT if there are genuine factual errors."
        )
        
        # ---- LLM se verification karwao ----
        # Temperature 0.3 rakha hai — verification mein creativity nahi chahiye
        # Strict aur factual hona chahiye
        verification_response = self.llm_client.generate(
            prompt=verification_prompt,
            system_prompt=system_prompt,
            temperature=0.3  # Low temp = strict/factual checking
        )
        
        # ---- Response parse karo ----
        # LLM ka text response ko structured data mein badlo
        result = self._parse_verification(verification_response, answer)
        
        return result
    
    def _parse_verification(self, response: str, original_answer: str) -> dict:
        """
        LLM ke verification response ko structured dict mein badlo.
        
        _ (underscore) function ke naam ke aage ka matlab:
        "Yeh PRIVATE function hai — sirf is class ke andar use hona chahiye"
        
        Jaise ghar ka andar ka kamra — bahar waale nahi aayenge.
        Python force nahi karta (just convention), but acchi practice hai.
        
        Parsing kya hai?
        ────────────────
        Text ko todna aur samajhna. Jaise:
        "VERDICT: CORRECT" → {"verdict": "CORRECT"}
        
        Hum LLM ke text response mein se keywords dhundh rahe hain.
        """
        
        response_upper = response.upper()
        
        # ---- Verdict nikalo ----
        if "INCORRECT" in response_upper and "PARTIALLY" not in response_upper:
            is_verified = False
            confidence = "low"
        elif "PARTIALLY_CORRECT" in response_upper or "PARTIALLY CORRECT" in response_upper:
            is_verified = True  # Mostly sahi hai
            confidence = "medium"
        else:
            # Default: CORRECT maan lo
            is_verified = True
            confidence = "high"
        
        # ---- Confidence override ----
        # Agar LLM ne explicitly confidence mention kiya hai
        if "CONFIDENCE: HIGH" in response_upper:
            confidence = "high"
        elif "CONFIDENCE: MEDIUM" in response_upper:
            confidence = "medium"
        elif "CONFIDENCE: LOW" in response_upper:
            confidence = "low"
        
        # ---- Result banao ----
        return {
            "is_verified": is_verified,
            "confidence": confidence,
            "feedback": response,           # Poora verification response
            "original_answer": original_answer,
            "verified_answer": original_answer if is_verified else response,
        }
