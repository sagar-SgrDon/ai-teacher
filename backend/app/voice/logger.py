"""
============================================================
VOICE MODULE: Logger — Sab Kuch Record Karo 📊
============================================================

📖 EXPLANATION:

Yeh file har voice conversation turn ka detailed log rakhti hai.
Production-level systems mein logging BAHUT important hai:

1. DEBUGGING: "Kya galat hua?" → logs dekho → turant pata chale
2. IMPROVEMENT: "LLM kitna slow hai?" → latency logs analyze karo
3. ANALYTICS: "Students ki common galtiyan?" → correction logs se pata karo
4. AUDITING: "Kab, kya, kaise?" → exact record available

JSONL format kya hai?
─────────────────────
JSON Lines = har line ek SEPARATE, COMPLETE JSON object.

Normal JSON file:
  [{"turn": 1, ...}, {"turn": 2, ...}]  ← poori file ek array
  Problem: file corrupt ho toh POORA data loss!

JSONL file:
  {"turn": 1, ...}    ← line 1 — independent
  {"turn": 2, ...}    ← line 2 — independent
  Crash ho toh SIRF last line affect — baaki safe!

Socho jaise diary mein har page alag — ek page fata toh
baaki diary safe. Normal JSON = spiral notebook jo ek piece hai.

FILE I/O CONCEPTS:
──────────────────
open(path, "a")  = "append" mode — file ke END mein likho (existing data safe)
open(path, "w")  = "write" mode — file POORI overwrite ho jaaye (cuidado!)
open(path, "r")  = "read" mode — sirf padho

"with open() as f:" kya hai?
────────────────────────────
Context manager — file automatic CLOSE hoti hai block khatam hone pe.
Bina "with" ke agar error aaye toh file open reh jaati — memory leak!
Socho jaise hotel ka kamra — checkout PE automatic lock ho jaata hai.

os.makedirs(exist_ok=True) kya hai?
───────────────────────────────────
Folder banao — agar pehle se hai toh error MAT do.
exist_ok=False hota toh pehle se folder hone pe crash ho jaata!
============================================================
"""

import json
import os
from datetime import datetime
from typing import Optional

# Path config import karo
from ..config import BACKEND_DIR


# ============================================================
# LOG DIRECTORY — Logs kahan save honge
# ============================================================
# backend/logs/voice_sessions/ mein har session ki alag file

LOG_DIR = os.path.join(BACKEND_DIR, "logs", "voice_sessions")


# ============================================================
# VOICE LOGGER — Main logging class
# ============================================================


class VoiceLogger:
    """
    Har voice conversation turn ka structured log maintain karo.

    Har session ki ek alag .jsonl file hoti hai:
      backend/logs/voice_sessions/{session_id}.jsonl

    Har line ek turn ka record hai — easily parseable.

    Singleton pattern kya hai?
    ─────────────────────────
    Ek hi instance banega poore app mein — sab jagah SAME logger use hoga.
    Hum yahan singleton nahi use kar rahe (simple rakha hai),
    but agar zarurat pade toh bana sakte hain.
    """

    def __init__(self):
        """
        Logger initialize karo — log directory banao agar nahi hai.

        os.makedirs() recursive hai — agar parent folders bhi nahi hain
        toh woh bhi bana deta hai.
        Jaise "mkdir -p" command Linux mein.
        """
        os.makedirs(LOG_DIR, exist_ok=True)
        print(f"✅ Voice Logger ready! Logs at: {LOG_DIR}")

    def _get_log_path(self, session_id: str) -> str:
        """
        Session ki log file ka path return karo.

        Har session ki ALAG file kyun?
        ─────────────────────────────
        1. Ek badi file mein 100 sessions ka data = mushkil dhundhna
        2. Alag files = session_id se direct file access — fast!
        3. Agar ek file corrupt ho toh baaki safe

        Socho jaise school mein har student ki alag file hoti hai,
        ek badi register mein sab nahi likhte.
        """
        return os.path.join(LOG_DIR, f"{session_id}.jsonl")

    def log_turn(
        self,
        session_id: str,
        turn_number: int,
        student_text: str,
        teacher_response: str,
        follow_up: str,
        corrections: list,
        latency: dict,
        session_state: dict,
        error: Optional[str] = None,
    ):
        """
        Ek complete turn ka log likho.

        Yeh method har turn ke baad call hoga — student bola,
        teacher ne jawab diya, corrections hui, kitna time laga.

        Parameters:
        ──────────
        session_id      : Kaunsi session ka log
        turn_number     : Yeh kaun sa turn hai (1, 2, 3...)
        student_text    : Student ne kya bola
        teacher_response: Teacher ne kya jawab diya
        follow_up       : Follow-up question kya tha
        corrections     : List of correction dicts
        latency         : {"stt_ms": 0, "llm_ms": 35000, "tts_ms": 2100, "total_ms": 37500}
        session_state   : {"mode": "free_talk", "level": "beginner", "topic": "..."}
        error           : Agar koi error aaya toh uska message (None = sab sahi)

        LATENCY kya hai?
        ────────────────
        Time measurement — kitna time laga kaam karne mein.
        STT latency = speech-to-text mein kitna time
        LLM latency = model ne jawab dene mein kitna time
        TTS latency = text-to-speech mein kitna time
        Total = poora cycle — end to end

        Latency important kyun hai?
        ──────────────────────────
        Production mein agar response 60 second le → user chhod dega!
        Latency track karne se pata chalta hai ki kaunsa part slow hai.
        "LLM 50s le raha hai" → solution: chhota model try karo
        "TTS 10s le raha hai" → solution: TTS optimize karo
        """

        log_entry = {
            "turn": turn_number,
            "timestamp": datetime.now().isoformat(),
            "student": student_text,
            "teacher": teacher_response,
            "follow_up": follow_up,
            "corrections": corrections,
            "latency": latency,
            "state": session_state,
            "error": error,
        }

        self._write_log(session_id, log_entry)

    def log_error(
        self,
        session_id: str,
        stage: str,
        error_message: str,
        details: Optional[dict] = None,
    ):
        """
        Error log likho — jab koi step fail ho.

        stage: Kaunsa step fail hua?
          "stt"  = Speech-to-Text fail
          "llm"  = LLM call fail (timeout, connection error)
          "tts"  = Text-to-Speech fail
          "parse" = JSON parsing fail
          "validation" = Data validation fail

        Error logs SEPARATE hain turn logs se kyunki:
        1. Turn log = normal operation ka record
        2. Error log = kuch GALAT hua ka record

        Socho hospital mein — normal treatment ki file alag,
        emergency ki file alag. Dono important hain.
        """

        log_entry = {
            "type": "error",
            "timestamp": datetime.now().isoformat(),
            "stage": stage,
            "error": error_message,
            "details": details or {},
        }

        self._write_log(session_id, log_entry)

        # Console pe bhi print karo — debugging ke liye
        print(f"   🐛 [{stage}] Error logged: {error_message}")

    def log_session_start(self, session_id: str, student_level: str):
        """
        Session start hone ka log — metadata record karo.

        Yeh pehla entry hota hai har session file mein.
        Jaise class register mein pehli entry: date, student name, etc.
        """

        log_entry = {
            "type": "session_start",
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "student_level": student_level,
        }

        self._write_log(session_id, log_entry)

    def log_session_summary(
        self,
        session_id: str,
        total_turns: int,
        total_corrections: int,
        mistake_counts: dict,
        final_level: str,
        total_duration_seconds: float,
    ):
        """
        Session khatam hone pe summary log likho.

        Yeh akhri entry hoti hai — poori class ka report card!

        Baad mein analytics ke liye useful hai:
        "Average session mein kitni corrections hoti hain?"
        "Students ka level kitna change hota hai?"
        "Average session kitni der chalti hai?"
        """

        log_entry = {
            "type": "session_summary",
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "total_turns": total_turns,
            "total_corrections": total_corrections,
            "mistake_counts": mistake_counts,
            "final_level": final_level,
            "total_duration_seconds": round(total_duration_seconds, 1),
        }

        self._write_log(session_id, log_entry)

    def _write_log(self, session_id: str, log_entry: dict):
        """
        Log entry ko file mein likho — JSONL format.

        APPEND mode ("a") use karte hain — existing data safe rahega.
        Har entry ke baad newline (\n) add karte hain — yahi
        JSONL format hai.

        try-except kyun?
        ────────────────
        File write fail ho sakta hai:
        - Disk full ho (no space)
        - Permission nahi hai (read-only)
        - Path galat hai

        Logging KABHI main process ko crash nahi karni chahiye!
        Agar log likhna fail ho toh bas print karo aur aage badho.
        Student ka experience logging ki wajah se kharab nahi hona chahiye.

        Socho — agar hospital mein register mein likghna fail ho
        toh doctor treatment band nahi karega!
        """
        try:
            log_path = self._get_log_path(session_id)

            with open(log_path, "a", encoding="utf-8") as f:
                # json.dumps() = Python dict → JSON string
                # ensure_ascii=False = Hindi/special characters sahi print honge
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

        except Exception as e:
            # Logging fail hone pe SIRF print karo — crash MAT karo!
            print(f"   ⚠️ Log write failed for {session_id[:8]}...: {e}")

    def get_session_logs(self, session_id: str) -> list:
        """
        Ek session ke saare logs padho — analytics/debugging ke liye.

        JSONL file line by line read karo → har line = ek dict.

        Returns:
            List of dicts — har dict ek log entry hai
        """
        log_path = self._get_log_path(session_id)

        if not os.path.exists(log_path):
            return []

        logs = []
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            logs.append(json.loads(line))
                        except json.JSONDecodeError:
                            # Corrupt line skip karo — baaki padho
                            continue
            return logs

        except Exception as e:
            print(f"   ⚠️ Log read failed: {e}")
            return []

    def get_session_stats(self, session_id: str) -> dict:
        """
        Session ke logs se quick stats nikalo.

        Yeh method logs padh ke ek summary dict banata hai:
        - Total turns
        - Total corrections
        - Average latencies
        - Error count

        Dashboard ya analytics ke liye useful hai.
        """
        logs = self.get_session_logs(session_id)

        if not logs:
            return {"error": "No logs found"}

        # Sirf turn logs filter karo (error aur session_start nahi)
        turn_logs = [
            log for log in logs if "turn" in log and log.get("type") != "error"
        ]
        error_logs = [log for log in logs if log.get("type") == "error"]

        if not turn_logs:
            return {"total_turns": 0, "total_errors": len(error_logs)}

        # Latency stats calculate karo
        total_ms_list = [
            turn_log["latency"]["total_ms"]
            for turn_log in turn_logs
            if "latency" in turn_log and "total_ms" in turn_log.get("latency", {})
        ]

        total_corrections = sum(
            len(turn_log.get("corrections", [])) for turn_log in turn_logs
        )

        stats = {
            "total_turns": len(turn_logs),
            "total_corrections": total_corrections,
            "total_errors": len(error_logs),
            "avg_latency_ms": round(sum(total_ms_list) / len(total_ms_list))
            if total_ms_list
            else 0,
            "min_latency_ms": round(min(total_ms_list)) if total_ms_list else 0,
            "max_latency_ms": round(max(total_ms_list)) if total_ms_list else 0,
        }

        return stats
