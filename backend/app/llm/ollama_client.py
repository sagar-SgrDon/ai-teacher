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

    def generate(
        self, prompt: str, system_prompt: str = None, temperature: float = 0.7
    ) -> str:
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
            "stream": False,  # Poora jawab ek baar mein (streaming nahi)
            "options": {
                "temperature": temperature,
                "num_predict": 1024,  # Maximum kitne words generate kare
                # 1024 tokens ≈ 750 words (roughly)
            },
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
                timeout=60,  # 2 minute max wait (phi3:mini thoda slow ho sakta hai)
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
            error_msg = (
                "Ollama se connect nahi ho pa raha! Kya 'ollama serve' chal raha hai?"
            )
            print(f"❌ {error_msg}")
            return f"Error: {error_msg}"

        except requests.Timeout:
            error_msg = "Ollama ne bahut zyada time le liya (timeout 120s)"
            print(f"❌ {error_msg}")
            return f"Error: {error_msg}"

        except:
            return json.dumps(
                {
                    "response": "Okay! Tell me more 😊",
                    "corrections": [],
                    "follow_up_question": "What do you mean?",
                }
            )    
        
    def generate_stream(
        self, prompt: str, system_prompt: str = None, temperature: float = 0.7
    ):
        """
        LLM se streaming jawab lo — word by word!

        STREAMING kya hai?
        ──────────────────
        Normal: Puri kitaab likho → phir ek baar mein de do
        Streaming: Ek ek line likhte jao → dete jao

        YouTube jaisa — poori video download nahi hoti,
        thoda thoda buffer hote hi dikhana shuru ho jaata hai!

        GENERATOR kya hai? (yield keyword)
        ──────────────────────────────────
        Normal function: return ek baar chalte hai, function khatam.
        Generator: yield baar baar chalta hai, function PAUSE hota hai,
                   phir wahi se continue karta hai.

        Socho jaise chai ki tapri:
        return = poori chai ek baar mein de do
        yield  = thoda thoda cup mein daalte jao
        """

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,  # ← YAHI farak hai! True = word by word
            "options": {
                "temperature": temperature,
                "num_predict": 1024,
            },
        }

        if system_prompt:
            payload["system"] = system_prompt

        try:
            # stream=True = response ek baar mein nahi, thoda thoda aayega
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=120,
                stream=True,  # ← requests library ko bolo: data stream karo
            )

            if response.status_code == 200:
                # iter_lines() = ek ek line padho jaise aaye
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line)
                        token = data.get("response", "")
                        if token:
                            yield token  # ← Har word TURANT bhejo!

                        # Jab "done" aa jaye = generation complete
                        if data.get("done", False):
                            break
            else:
                yield f"Error: Ollama status {response.status_code}"

        except requests.ConnectionError:
            yield "Error: Ollama se connect nahi ho pa raha!"
        except requests.Timeout:
            yield "Error: Timeout — 120s se zyada time lag gaya"

    def build_rag_prompt(
        self, question: str, context: str, teacher_type: str = "english"
    ) -> tuple:
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

    # ============================================================
    # VOICE CONVERSATION METHODS — Emma Teacher Ke Liye
    # ============================================================
    #
    # Yeh methods voice conversation ke liye SPECIALLY designed hain.
    # Text chat se kya farak hai?
    #
    # TEXT CHAT:
    #   - Single question → single answer
    #   - No memory (har question alag hai)
    #   - Free text output (kuch bhi bol do)
    #
    # VOICE CONVERSATION:
    #   - Multi-turn (pichli baatein yaad hai)
    #   - Structured JSON output (parse karna hai)
    #   - State-aware (mode, topic, level)
    #   - Follow-up mandatory (conversation rukna nahi chahiye)
    #   - Word limit (80 words — voice mein lamba boring)

    def generate_voice_response(
        self,
        prompt: str,
        system_prompt: str,
        temperature: float = 0.7,
        timeout: int = 60,
    ) -> str:
        """
        Voice conversation ke liye LLM se jawab lo — JSON mode mein!

        TEXT chat ke generate() se 2 BADE differences:
        ───────────────────────────────────────────────
        1. "format": "json" → Ollama ko bolo: "SIRF JSON bhejo,
           kuch aur mat bhejo". Yeh Ollama ka built-in feature hai.
           Bina iske LLM kabhi JSON bhejta kabhi nahi — unpredictable!

        2. timeout = 60 seconds (text mein 120 seconds tha)
           Voice mein user wait kar raha hai (mic se bola hai) →
           jaldi jawab chahiye. 60s se zyada = user chhod dega.
           Timeout hone pe fallback response jaayega.

        JSON MODE kya hai? (Ollama feature)
        ────────────────────────────────────
        Normally LLM kuch bhi generate karta — text, markdown, JSON, etc.
        "format": "json" lagane se Ollama FORCE karta hai ki output
        valid JSON ho. Internally yeh token probabilities adjust karta hai
        taaki sirf JSON-valid tokens generate hon.

        Socho jaise exam mein MCQ hai — answer A, B, C, D mein se hi
        dena hai, essay nahi likh sakte. JSON mode = MCQ mode.

        Parameters:
            prompt       : Full prompt with conversation history
            system_prompt: Emma teacher ka personality
            temperature  : Creativity level (0.7 = balanced)
            timeout      : Max wait time in seconds (60s for voice)

        Returns:
            str: LLM ka raw output (hopefully JSON, but parse zaroori!)
        """

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",  # ← YAHI magic hai! JSON force karo
            "options": {
                "temperature": temperature,
                "num_predict": 512,  # Voice ke liye chhota output (80 words ≈ 100-150 tokens)
                # 512 tokens = safe margin with corrections JSON
            },
        }

        if system_prompt:
            payload["system"] = system_prompt

        try:
            import time

            start = time.perf_counter()

            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=timeout,  # ← 60s timeout (text mein 120s tha)
            )

            duration = time.perf_counter() - start

            if response.status_code == 200:
                data = response.json()
                answer = data.get("response", "").strip()
                print(f"   ⏱️ Voice LLM response: {duration:.1f}s")
                return answer
            else:
                print(f"   ❌ Ollama error: {response.status_code}")
                return ""

        except requests.Timeout:
            # 60s timeout — fallback JSON return karo
            # Student wait kar raha hai, kuch toh bolna chahiye!
            print(f"   ⏱️ LLM TIMEOUT ({timeout}s)! Returning fallback.")
            return json.dumps(
                {
                    "response": "That's interesting! Let me think about that.",
                    "corrections": [],
                    "follow_up_question": "Could you tell me more about what you mean?",
                }
            )

        except requests.ConnectionError:
            print("   ❌ Ollama se connect nahi ho pa raha!")
            return ""

    def build_voice_conversation_prompt(
        self,
        student_message: str,
        conversation_context: str,
        rag_context: str,
        state: dict,
        native_language: str = "english",
    ) -> tuple:
        """
        Voice conversation ke liye FULL prompt banao.

        Yeh method sab kuch ek jagah combine karta hai:
        - Emma teacher ka personality (system_prompt)
        - Conversation state (mode, topic, goal)
        - Conversation history (summary + recent turns)
        - RAG teaching material
        - Student ka current message
        - Output format instructions (JSON schema)

        Pehle waale build_rag_prompt() se kya farak?
        ──────────────────────────────────────────────
        build_rag_prompt() = Simple Q&A (question + context)
        build_voice_conversation_prompt() = Rich conversation
          (history + state + corrections + context + question)

        Socho aise:
        build_rag_prompt() = Stranger se ek sawaal poocha
        build_voice_conversation_prompt() = Apne teacher se ongoing class

        Parameters:
            student_message      : Student ne abhi kya bola
            conversation_context : get_context() se mila summary + recent turns
            rag_context          : RAG se mili teaching material
            state                : get_state_for_prompt() se mila state dict

        Returns:
            tuple: (prompt, system_prompt) — generate_voice_response() ko dena
        """

        # Error types ki list — prompt mein inject karo
        # taaki LLM ko pata rahe kaunse options hain
        from ..voice.conversation_manager import ErrorType

        error_types_str = ", ".join([e.value for e in ErrorType])

        # ============================================================
        # SYSTEM PROMPT — Emma Teacher Ka Personality Card
        # ============================================================
        #
        # Yeh LLM ko batata hai: "TU KAUN HAI aur KAISE behave karna hai"
        #
        # System prompt ka role bahut important hai:
        # - Bina system prompt ke: LLM generic assistant hai
        # - System prompt ke saath: LLM Emma teacher BAN jaata hai
        #
        # Socho jaise actor ko script di jaati hai —
        # "tu doctor hai, patient se aise baat kar" — waise hi!

        # ---- Native language instructions ----
        # Yeh LLM ko batata hai ki explanations kis language mein deni hain
        if native_language == "hinglish":
            language_instruction = """
        CRITICAL — LANGUAGE RULE (MUST FOLLOW):
        You MUST speak in HINGLISH (Hindi + English mix) in all your responses.
        DO NOT speak in pure English. Mix Hindi words naturally.
        
        HINGLISH EXAMPLES (copy this style):
        - "Dekho, 'goes' nahi chalega yahan. Past ki baat hai toh 'went' use karo. Samjhe?"
        - "Bahut accha! Tumne sahi bola. Ab ek aur sentence try karo."
        - "Yeh common galti hai. 'I go' hota hai, 'I goes' nahi. Yaad rakhna!"
        
        RULES:
        - 'response' field MUST be in Hinglish (Hindi + English mix)
        - 'explanation' in corrections MUST be in Hinglish
        - 'follow_up_question' MUST be in Hinglish
        - 'original' and 'corrected' stay in English (they are English sentences)
        - Use phrases like: Dekho, Samjhe?, Bilkul sahi!, Bahut accha!, Chalo, Socho"""
            teacher_desc = (
                "English teacher who ALWAYS explains in Hinglish (Hindi-English mix)"
            )
        elif native_language == "hindi":
            language_instruction = """
        CRITICAL — LANGUAGE RULE (MUST FOLLOW):
        You MUST speak in HINDI for explanations. Use English only for grammar terms and example sentences.
        
        HINDI EXAMPLES (copy this style):
        - "यहाँ 'goes' गलत है। बीते हुए कल की बात है तो 'went' लगाओ। सही वाक्य: 'I went to school yesterday.'"
        - "बहुत अच्छा! शाबाश! एक और वाक्य बनाओ।"
        
        RULES:
        - 'response' field MUST be in Hindi
        - 'explanation' in corrections MUST be in Hindi 
        - 'follow_up_question' MUST be in Hindi
        - 'original' and 'corrected' stay in English"""
            teacher_desc = "English teacher who ALWAYS explains in Hindi"
        else:
            language_instruction = """
        LANGUAGE STYLE:
        - Speak in clear, simple English.
        - Use short sentences appropriate for the student's level."""
            teacher_desc = "English speaking teacher"

        system_prompt = f"""You are Emma, a warm, encouraging, and highly skilled {teacher_desc}.
        You are having a VOICE CONVERSATION with a student learning English.
        {language_instruction}

        YOUR TEACHING RULES:
        1. Sound like a REAL teacher in a live conversation, not a grammar checker.
        2. First understand the student's intent and emotion. If the student sounds confused, annoyed, or asks what you mean, clarify gently before teaching anything.
        3. Correct ONLY when it genuinely helps. Prefer 0 or 1 correction. Use 2 only if both mistakes are critical.
        4. Do NOT force a correction on every turn. If the student is expressing an idea, respond to the idea first.
        5. Ask a follow-up question ONLY when it feels natural and useful. It is okay to leave follow_up_question empty.
        6. Keep responses SHORT — max 60-80 words total. This is spoken conversation, not an essay.
        7. Be ENCOURAGING and calm. Never sound scolding, repetitive, or robotic.
        8. If this is a repeated mistake, do a tiny drill naturally, but keep the conversation flowing.
        9. Adapt language complexity to student level: {state.get("student_level", "beginner")}

        CORRECTION STYLE:
        - Prefer recasts over lectures. Example: student says something imperfect, you reply naturally with the better version.
        - Never invent strange English translations just to create a correction.
        - If the student's sentence is mostly understandable, don't over-correct.
        - If the student asks a meta question like "what are you saying?" or "teach properly", answer that directly.

        RESPONSE RULES:
        - error_type MUST be one of: {error_types_str}
        - Usually 0 or 1 correction, maximum 2
        - follow_up_question may be empty"""
        # ============================================================
        # USER PROMPT — Sab context + question combine karo
        # ============================================================
        #
        # Prompt engineering ka golden rule:
        # CLEAR structure do → LLM accha output dega
        #
        # Hum prompt ko sections mein divide karte hain:
        # 1. STATE — teacher ka current mode kya hai
        # 2. CONTEXT — pichli conversation ka summary
        # 3. MATERIAL — RAG se mila teaching material
        # 4. MESSAGE — student ne abhi kya bola
        # 5. FORMAT — output kaise chahiye (JSON schema)

        prompt = f"""CURRENT STATE:
        - Mode: {state.get("mode", "free_talk")}
        - Topic: {state.get("current_topic", "general_conversation")}
        - Goal: {state.get("turn_goal", "teach_concept")}
        - Student Level: {state.get("student_level", "beginner")}
        - Repeated Mistakes: {state.get("repeated_mistakes", "none")}

        CONVERSATION HISTORY:
        {conversation_context}

        TEACHING MATERIAL (from knowledge base):
        {rag_context if rag_context else "No specific teaching material available for this topic."}

        STUDENT JUST SAID: "{student_message}"

        RESPOND AS EMMA IN THIS EXACT JSON FORMAT (no markdown, no extra text):
        {{"response": "<your teaching response, max 80 words>", "corrections": [{{"original": "<what student said wrong>", "corrected": "<correct version>", "error_type": "<from the allowed list>", "explanation": "<brief why>"}}], "follow_up_question": "<optional natural follow-up or empty string>"}}

        If the student made no important mistakes, use an empty corrections array: "corrections": []`n        If no natural follow-up is needed, use: "follow_up_question": ""
        {self._get_language_example(native_language)}
        JSON ONLY:"""

        return prompt, system_prompt

    @staticmethod
    def _get_language_example(native_language: str) -> str:
        """
        Few-shot example return karo — small models ke liye BEST technique.

        Kyun? phi3:mini jaise models instructions se zyada EXAMPLES se seekhte hain.
        Agar dikhao "Hinglish JSON aisa dikhta hai" toh woh copy karega.
        """
        if native_language == "hinglish":
            return """
        IMPORTANT: Write response, explanation, follow_up_question in HINGLISH like this example:`n        EXAMPLE (copy this Hinglish style):`n        {"response": "Samajh gaya tum kya kehna chah rahe ho. Natural English mein hum bolenge: 'Delhi is a very crowded city.' Tumhari idea sahi thi, bas sentence ko thoda smooth banana tha.", "corrections": [{"original": "Delhi to bahut bheed bahar wali jagah hai", "corrected": "Delhi is a very crowded city", "error_type": "vocabulary_choice", "explanation": "Meaning same hai, bas English mein isse zyada natural tarike se bolte hain."}], "follow_up_question": "What do you like about Delhi?"}`n`n        Keep the tone natural, warm, and teacher-like. Don't keep repeating filler words like 'dekho' or 'samjhe' in every answer."""
        elif native_language == "hindi":
            return """
        IMPORTANT: Write response, explanation, follow_up_question in HINDI like this example:`r`n        EXAMPLE (copy this Hindi style):`r`n        {"response": "मैं समझ गया कि आप क्या कहना चाहते हैं। Natural English में हम कहेंगे: 'Delhi is a very crowded city.' आपकी बात सही थी, बस sentence को थोड़ा smooth बनाना था।", "corrections": [{"original": "Delhi to bahut bheed bahar wali jagah hai", "corrected": "Delhi is a very crowded city", "error_type": "vocabulary_choice", "explanation": "अर्थ वही है, बस English में इसे अधिक natural तरह से बोलते हैं।"}], "follow_up_question": "What do you like about Delhi?"}"""
        else:
            return ""

    def build_voice_retry_prompt(self, student_message: str) -> tuple:
        """
        Jab pehli baar LLM ne valid JSON nahi diya → STRICTER prompt se dubara poocho.

        Pehle prompt se kya farak?
        ──────────────────────────
        1. Bahut CHHOTA prompt — kam cheezein = kam confusion
        2. Explicitly bola: "ONLY JSON, NOTHING ELSE"
        3. Example diya — LLM ko dikhaya exact output kya chahiye
        4. Error types listed — copy-paste kar sake

        RETRY PATTERN kya hai?
        ─────────────────────
        Pehli attempt: Full detailed prompt → LLM confused ho sakta hai
        Retry attempt: Simplified, focused prompt → better chance of correct output

        Socho exam mein — pehla question samajh nahi aaya.
        Examiner bola: "Arre bas itna batao: X kya hai? Ek line mein."
        Simple poocha → simple jawab mila.
        """

        from ..voice.conversation_manager import ErrorType

        error_types_str = ", ".join([e.value for e in ErrorType])

        system_prompt = (
            "You are Emma, an English teacher. Respond ONLY in valid JSON format."
        )

        prompt = f"""Your previous response was not valid JSON. 
        Respond with ONLY a JSON object. No markdown. No explanation. No extra text.

        EXACT FORMAT:
        {{"response": "<your teaching response, max 80 words>", "corrections": [{{"original": "<what student said wrong>", "corrected": "<correct version>", "error_type": "<MUST be one of: {error_types_str}>", "explanation": "<brief why>"}}], "follow_up_question": "<always ask a follow-up question>"}}

        If no corrections needed, use empty array: "corrections": []

        Student said: "{student_message}"

        JSON ONLY:"""

        return prompt, system_prompt
