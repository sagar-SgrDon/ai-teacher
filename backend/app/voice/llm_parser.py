"""
============================================================
VOICE MODULE: LLM Parser — LLM Ka Output Check Karo 🔍
============================================================

📖 EXPLANATION:

LLM (phi3:mini) se hum JSON format mein jawab maangte hain:
{
    "response": "teacher ka jawab",
    "corrections": [...],
    "follow_up_question": "agle question"
}

PROBLEM: LLM hamesha sahi JSON nahi bhejta!
Kabhi markdown mein wrap kar deta hai → ```json {...} ```
Kabhi extra text likh deta hai → "Here is your response: {...}"
Kabhi toh JSON hi nahi bhejta → seedha plain text!

SOLUTION: Robust parsing chain:
1. Try: json.loads(raw_text)           → happy path ✅
2. Try: regex se {...} extract karo     → markdown wrapped ✅
3. Try: LLM ko dobara poocho (stricter prompt)  → retry ✅
4. Fallback: raw text ko response mein daal do  → never crash ✅

Parse ke BAAD validation:
- error_type enum mein hai? Nahi → correction DROP karo ❌
- corrections 2 se zyada? → cap at 2 ✂️
- follow_up empty? → default daal do 🔄
- response 80 words se zyada? → truncate karo ✂️
- Same correction last turn mein thi? → debounce (skip) 🔕

REGEX kya hai?
──────────────
Regular Expression = text mein patterns dhundhne ka tool.
Jaise CTRL+F se words dhundhte ho, regex se PATTERNS dhundhte ho.
Pattern: \{.*\} ka matlab: "curly braces ke andar jo bhi ho, dhoondho"

re.DOTALL kya hai?
──────────────────
Normally "." newline (\n) ko match nahi karta.
re.DOTALL lagane se "." NEWLINE BHI match karta hai.
Zaruri hai kyunki JSON multi-line ho sakta hai.
============================================================
"""

import json
import re
from typing import Optional
from dataclasses import dataclass, field

# Apne conversation_manager se imports
from .conversation_manager import ErrorType, Correction


# ============================================================
# VALID ERROR TYPES — Quick lookup set
# ============================================================
# Set kya hai?
# ────────────
# Set = unique items ka collection, aur BAHUT FAST lookup hota hai.
# List mein dhundhna = ek ek check karo (slow) 🐌
# Set mein dhundhna = DIRECTLY check (fast) ⚡
# 
# "tense_agreement" in VALID_ERROR_TYPES → instant answer!

VALID_ERROR_TYPES = {e.value for e in ErrorType}
# Result: {"tense_agreement", "article_usage", "preposition", ...}


# ============================================================
# PARSED RESPONSE — LLM ka clean, validated output
# ============================================================

@dataclass
class ParsedTeacherResponse:
    """
    LLM ka parsed + validated response.
    
    Yeh final output hai jo baaki system use karega.
    Raw LLM text → parse → validate → yeh object banta hai.
    
    Socho jaise raw maal factory mein jaata hai →
    quality check hota hai → packaged product bahar aata hai.
    Yeh "packaged product" hai.
    """
    response: str                              # Teacher ka jawab
    corrections: list = field(default_factory=list)  # Validated corrections (max 2)
    follow_up_question: str = "Can you tell me more about that?"  # Default follow-up
    tts_text: str = ""                         # Merged text for TTS (response + follow_up)
    parse_success: bool = True                 # Kya parse hua ya fallback use hua
    raw_llm_output: str = ""                   # Original LLM output (debugging ke liye)


# ============================================================
# MAX LIMITS — Response ko control karo
# ============================================================

MAX_CORRECTIONS_PER_TURN = 2    # Ek turn mein max 2 corrections
                                 # Zyada ho toh student overwhelm ho jaayega

MAX_RESPONSE_WORDS = 80         # Voice mein 80 words max — zyada lamba boring
                                 # 80 words ≈ 30-40 seconds of speech

DEFAULT_FOLLOW_UP = "Can you tell me more about that?"  
                                 # Jab LLM follow_up na de toh yeh use karo


# ============================================================
# MAIN PARSER FUNCTION — LLM output ko parse + validate karo
# ============================================================

def parse_llm_response(raw_text: str) -> ParsedTeacherResponse:
    """
    LLM ka raw text output → clean, validated ParsedTeacherResponse.
    
    PARSING CHAIN (pehla jo kaam kare, wahi use karo):
    ──────────────────────────────────────────────────
    1. json.loads(raw_text) — direct parse (happy path)
    2. Regex se {...} extract → json.loads — markdown wrapped
    3. Fallback — raw text ko response mein daal do
    
    VALIDATION (parse ke baad):
    ──────────────────────────
    - error_type check: enum mein nahi → DROP correction
    - corrections cap: max 2
    - follow_up guarantee: empty → default
    - word count cap: > 80 → truncate
    - TTS merge: response + follow_up → ek string
    
    Parameters:
        raw_text: LLM se aaya hua raw string
    
    Returns:
        ParsedTeacherResponse — validated, capped, ready to use
    """
    
    parsed_json = None
    
    # ---- Attempt 1: Direct JSON parse ----
    # Best case — LLM ne seedha JSON bheja
    parsed_json = _try_direct_parse(raw_text)
    
    # ---- Attempt 2: Regex extract ----
    # LLM ne JSON ko markdown ya extra text mein wrap kiya
    if parsed_json is None:
        parsed_json = _try_regex_extract(raw_text)
    
    # ---- Attempt 3: Fallback ----
    # Kuch bhi kaam nahi aaya — raw text ko response banao
    if parsed_json is None:
        print("   ⚠️ JSON parse failed! Using fallback response.")
        return ParsedTeacherResponse(
            response=_clean_raw_text(raw_text),
            corrections=[],
            follow_up_question=DEFAULT_FOLLOW_UP,
            tts_text=f"{_clean_raw_text(raw_text)} {DEFAULT_FOLLOW_UP}",
            parse_success=False,
            raw_llm_output=raw_text
        )
    
    # ---- JSON mila! Ab validate karo ----
    return _validate_and_build(parsed_json, raw_text)


def parse_llm_response_with_retry(
    raw_text: str, 
    retry_func: callable = None,
    student_message: str = ""
) -> ParsedTeacherResponse:
    """
    Parse karo — agar fail ho toh RETRY karo stricter prompt se.
    
    RETRY STRATEGY:
    ───────────────
    Pehli baar: Normal parse attempt
    Doosri baar: LLM ko DOBARA poocho ek STRICTER prompt se
    
    Stricter prompt mein kya farak hai?
    - Explicitly bolo: "ONLY JSON, no markdown"
    - Exact schema dikhao
    - Chhota prompt — kam confusion
    
    Socho jaise exam mein student ne answer galat format mein likha,
    toh teacher bole: "dubara likho, IS format mein likho" — 
    aur zyada strict instructions de.
    
    Parameters:
        raw_text: LLM ka pehla output
        retry_func: function jo stricter prompt se LLM ko dobara call kare
                    → signature: retry_func(student_message) -> str
        student_message: student ne kya bola tha (retry ke liye zaruri)
    """
    
    # ---- Pehli baar try karo ----
    result = parse_llm_response(raw_text)
    
    # Agar parse success hua → return (khush!)
    if result.parse_success:
        return result
    
    # ---- Parse fail — RETRY karo ----
    if retry_func and student_message:
        print("   🔄 Retrying with stricter prompt...")
        
        try:
            retry_text = retry_func(student_message)
            retry_result = parse_llm_response(retry_text)
            
            if retry_result.parse_success:
                print("   ✅ Retry successful!")
                return retry_result
            else:
                print("   ❌ Retry bhi fail hua. Using fallback.")
        except Exception as e:
            print(f"   ❌ Retry error: {e}")
    
    # Dono attempts fail — pehla fallback result return karo
    return result


# ============================================================
# INTERNAL HELPERS — Parse ke tools
# ============================================================

def _try_direct_parse(text: str) -> Optional[dict]:
    """
    Seedha json.loads() try karo.
    
    json.loads() kya karta hai?
    ──────────────────────────
    JSON string → Python dictionary mein convert karta hai.
    '{"name": "Rahul"}' → {"name": "Rahul"}
    
    Agar input valid JSON nahi hai toh ValueError deta hai.
    Hum try-except se isse handle karte hain.
    """
    try:
        # strip() = extra whitespace hatao (shuru aur end se)
        parsed = json.loads(text.strip())
        
        # Check: kya yeh dict hai? (JSON object chai hiye, array nahi)
        if isinstance(parsed, dict) and "response" in parsed:
            return parsed
        
        return None
    except (json.JSONDecodeError, ValueError):
        return None


def _try_regex_extract(text: str) -> Optional[dict]:
    """
    Regex se pehla {...} block extract karo, phir parse karo.
    
    Yeh kyun chahiye?
    ─────────────────
    LLM aksar JSON ko markdown mein wrap kar deta hai:
    ```json
    {"response": "..."}
    ```
    
    Ya extra text likhta hai:
    "Here is the response: {"response": "..."}"
    
    Regex se hum sirf {...} extract kar lete hain.
    
    REGEX pattern: r'\{.*\}'
    ──────────────────────
    \{  = literal { dhundho (curly brace)
    .*  = beech mein kuch bhi ho (any character, any count)
    \}  = literal } dhundho
    
    re.DOTALL = "." newline ko bhi match kare (multi-line JSON ke liye)
    """
    try:
        # Pehla JSON object dhundho
        match = re.search(r'\{.*\}', text, re.DOTALL)
        
        if match:
            json_str = match.group(0)  # matched text nikalo
            parsed = json.loads(json_str)
            
            if isinstance(parsed, dict) and "response" in parsed:
                return parsed
        
        return None
    except (json.JSONDecodeError, ValueError):
        return None


def _clean_raw_text(text: str) -> str:
    """
    Raw LLM text se markdown artifacts hatao.
    
    Jab LLM plain text bhejta hai (JSON nahi), tab us text ko 
    seedha response mein use karte hain. Pehle thoda clean karo:
    - Markdown code blocks hatao (```json ... ```)
    - Extra whitespace hatao
    - Bahut lamba ho toh truncate karo
    """
    # Markdown code blocks hatao
    text = re.sub(r'```[\w]*\n?', '', text)
    
    # Extra whitespace clean karo
    text = ' '.join(text.split())
    
    # Truncate if needed
    text = _truncate_to_words(text, MAX_RESPONSE_WORDS)
    
    return text.strip()


# ============================================================
# VALIDATION — Parse ke baad quality check
# ============================================================

def _validate_and_build(parsed: dict, raw_text: str) -> ParsedTeacherResponse:
    """
    Parsed JSON ko validate karo aur final response banao.
    
    Yeh function 4 cheezein check karta hai:
    1. Corrections mein error_type valid hai? (enum check)
    2. Corrections 2 se zyada toh nahi? (cap)
    3. Follow-up question hai? (guarantee)
    4. Response 80 words se zyada toh nahi? (word cap)
    
    Socho aise — factory mein product banne ke baad QA team check karti hai:
    "Colour sahi hai?" ✅
    "Size sahi hai?" ✅
    "Packaging theek hai?" ✅
    Sab pass ho toh dispatch hota hai.
    """
    
    # ---- 1. Response extract karo ----
    response = parsed.get("response", "").strip()
    if not response:
        response = "That's an interesting point!"
    
    # ---- 2. Corrections validate karo ----
    raw_corrections = parsed.get("corrections", [])
    valid_corrections = _validate_corrections(raw_corrections)
    
    # ---- 3. Follow-up guarantee ----
    follow_up = parsed.get("follow_up_question", "").strip()
    if not follow_up:
        follow_up = DEFAULT_FOLLOW_UP
        # Log kyunki yeh LLM ki galti hai — usne follow_up nahi diya
        print("   ⚠️ LLM ne follow_up nahi diya — default use kar rahe hain")
    
    # ---- 4. Word count cap ----
    response = _truncate_to_words(response, MAX_RESPONSE_WORDS)
    
    # ---- 5. TTS text merge ----
    # Response + follow_up = ek natural sentence for speech
    # "Your sentence was great! Now, can you tell me about your day?"
    tts_text = f"{response} {follow_up}"
    
    return ParsedTeacherResponse(
        response=response,
        corrections=valid_corrections,
        follow_up_question=follow_up,
        tts_text=tts_text,
        parse_success=True,
        raw_llm_output=raw_text
    )


def _validate_corrections(raw_corrections: list) -> list:
    """
    Corrections ko validate karo:
    1. Har correction mein required fields hain? (original, corrected, error_type, explanation)
    2. error_type VALID hai? (enum mein hai?)
    3. Max 2 corrections (cap)
    
    STRICT VALIDATION:
    ──────────────────
    Agar error_type enum mein nahi hai → POORI correction DROP karo!
    Silently accept NAHI karenge — kyunki galat error_type se 
    tracking barbaad ho jaayegi.
    
    Socho aise — agar koi bank mein galat account number de, 
    toh bank transaction REJECT karta hai, silently kisi random 
    account mein transfer nahi karta!
    """
    valid = []
    
    for i, corr in enumerate(raw_corrections):
        # ---- Required fields check ----
        if not isinstance(corr, dict):
            print(f"   ⚠️ Correction {i+1}: dict nahi hai, skip")
            continue
        
        original = corr.get("original", "").strip()
        corrected = corr.get("corrected", "").strip()
        error_type_str = corr.get("error_type", "").strip()
        explanation = corr.get("explanation", "").strip()
        
        # Koi bhi field empty → skip
        if not all([original, corrected, error_type_str]):
            print(f"   ⚠️ Correction {i+1}: required fields missing, skip")
            continue
        
        # ---- STRICT enum validation ----
        # error_type MUST be in our enum — warna REJECT!
        if error_type_str not in VALID_ERROR_TYPES:
            print(f"   ❌ Correction {i+1}: error_type '{error_type_str}' INVALID! Dropping.")
            continue
        
        # ---- Default explanation ----
        if not explanation:
            explanation = f"'{original}' should be '{corrected}'"
        
        # Sab sahi hai → add karo
        valid.append({
            "original": original,
            "corrected": corrected,
            "error_type": error_type_str,
            "explanation": explanation
        })
        
        # ---- Max 2 corrections cap ----
        if len(valid) >= MAX_CORRECTIONS_PER_TURN:
            if len(raw_corrections) > MAX_CORRECTIONS_PER_TURN:
                print(f"   ✂️ {len(raw_corrections)} corrections mili, capping to {MAX_CORRECTIONS_PER_TURN}")
            break
    
    return valid


def _truncate_to_words(text: str, max_words: int) -> str:
    """
    Text ko max_words pe truncate karo — last complete sentence pe.
    
    Kyun sentence pe?
    ─────────────────
    Agar beech sentence mein kaat do toh awaaz mein ajeeb lagega:
    "I think you should try to use the present tense because—" ✂️ (Cut!)
    
    Better: "I think you should try to use the present tense." ✅
    
    split() kya karta hai?
    ─────────────────────
    String ko spaces pe tod ke list banata hai.
    "Hello world" → ["Hello", "world"]
    len() se word count milta hai.
    """
    words = text.split()
    
    if len(words) <= max_words:
        return text
    
    # Max words tak le lo
    truncated = ' '.join(words[:max_words])
    
    # Last complete sentence dhundho (last period/question mark/exclamation)
    last_sentence_end = max(
        truncated.rfind('.'),
        truncated.rfind('!'),
        truncated.rfind('?')
    )
    
    # Agar koi sentence boundary mili toh wahan kaat do
    if last_sentence_end > len(truncated) // 2:  # at least halfway
        truncated = truncated[:last_sentence_end + 1]
    
    return truncated


# ============================================================
# UTILITY: Correction dict → Correction object
# ============================================================

def dict_to_correction(corr_dict: dict, turn_number: int) -> Optional[Correction]:
    """
    Validated correction dict → Correction dataclass object.
    
    Yeh function validated dict ko proper Correction object 
    mein convert karta hai — conversation_manager mein store 
    karne ke liye.
    
    Kyun alag function?
    ──────────────────
    Separation of concerns — parse karna alag, store karna alag.
    Parser sirf dicts deta hai (lightweight).
    Yeh function dicts ko proper objects mein badalta hai.
    """
    try:
        error_type = ErrorType(corr_dict["error_type"])
        
        return Correction(
            original=corr_dict["original"],
            corrected=corr_dict["corrected"],
            error_type=error_type,
            explanation=corr_dict["explanation"],
            turn_number=turn_number
        )
    except (ValueError, KeyError) as e:
        print(f"   ⚠️ Correction object nahi ban paaya: {e}")
        return None


# ============================================================
# UTILITY: Text normalize karo (STT output ke liye)
# ============================================================

def normalize_text(text: str) -> str:
    """
    STT se aaya text clean karo — LLM ko bhejne se pehle.
    
    Kyun normalize karna hai?
    ────────────────────────
    Whisper kabhi kabhi extra spaces, weird punctuation, 
    ya trailing noise add karta hai.
    
    Clean input → better LLM output.
    Socho jaise exam mein saaf likhoge toh teacher ko padhne 
    mein aasani — aur marking bhi acchi milegi!
    
    .strip() = shuru aur end ke spaces hatao
    .lower() = sab lowercase karo (consistency ke liye)
    split() + join() = multiple spaces ko ek space mein badlo
    """
    if not text:
        return ""
    
    # Basic cleanup
    text = text.strip()
    
    # Multiple spaces → single space
    text = ' '.join(text.split())
    
    # Lowercase for consistency
    text = text.lower()
    
    return text


# ============================================================
# UTILITY: Build retry prompt (stricter)
# ============================================================

def build_retry_prompt(student_message: str) -> str:
    """
    Jab pehli baar LLM ne valid JSON nahi diya, toh STRICTER 
    prompt banao retry ke liye.
    
    Pehle prompt se kya farak hai?
    ──────────────────────────────
    1. Explicitly bola: "ONLY JSON, no markdown, no extra text"
    2. Exact error_type values listed (copy-paste karne ke liye)
    3. Chhota prompt — kam confusion chance
    4. Example diya — LLM ko dikhaya exact format kya chahiye
    
    Socho aise — pehli baar student ko bola "essay likho".
    Galat format mein likha.
    Doosri baar bola: "SIRF yeh format use karo, yeh example 
    dekho, ALAG se kuch mat likho."
    """
    
    # Error type values ki list — LLM ko dikhao exact options
    error_types_str = ", ".join([e.value for e in ErrorType])
    
    return f"""Your previous response was not valid JSON. 
Respond with ONLY a JSON object. No markdown. No explanation. No extra text.

EXACT FORMAT:
{{"response": "<your teaching response, max 80 words>", "corrections": [{{"original": "<what student said wrong>", "corrected": "<correct version>", "error_type": "<MUST be one of: {error_types_str}>", "explanation": "<brief why>"}}], "follow_up_question": "<always ask a follow-up question>"}}

If no corrections needed, use empty array: "corrections": []

Student said: "{student_message}"

JSON ONLY:"""
