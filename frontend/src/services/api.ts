/**
 * API Service — Backend se communication
 *
 * Axios kya hai?
 * ──────────────
 * fetch() ka BETTER version:
 * - Auto JSON parse (response.json() likhne ki zaroorat nahi)
 * - Interceptors (har request mein token add karo automatically)
 * - Better error handling
 * - Timeout support
 *
 * Python mein requests library jaisa hai!
 */

import axios from "axios";

// Backend ka address — FastAPI server yahan chal raha hai
const API_BASE = "http://localhost:8000";

// Axios instance banao — ek baar config karo, baar baar use karo
const api = axios.create({
  baseURL: API_BASE,
  timeout: 120000, // 120 seconds max wait (LLM slow hai)
  headers: {
    "Content-Type": "application/json",
  },
});

// ============================================================
// Types — Response ka shape define karo
// ============================================================

export interface AskRequest {
  question: string;
  teacher_type: "english" | "coding";
  verify: boolean;
}

export interface AskResponse {
  answer: string;
  confidence: string;
  is_verified: boolean;
  sources: string[];
  teacher: string;
}

export interface HealthResponse {
  status: string;
  ollama: string;
  teachers: string[];
}

// ============================================================
// VOICE TYPES — Voice endpoints ke liye TypeScript types
// ============================================================
//
// TypeScript mein interfaces = blueprints
// Socho jaise form ka template — backend ko kya bhejenge
// aur backend se kya aayega, woh pehle se define karo.
//
// Iska fayda? IDE mein auto-complete milta hai aur
// galat data bhejne pe INSTANTLY error dikhta hai (runtime nahi, compile time pe!)

/**
 * Voice session start karne ka request
 *
 * student_level: Student ki English skill
 *   "beginner"      → Basic grammar, simple words
 *   "intermediate"  → Complex sentences, idioms
 *   "advanced"      → Fluent conversation, subtle errors
 *
 * native_language: Emma kis language mein baatein karegi
 *   "english"   → Pure English (default)
 *   "hinglish"  → Hindi-English mix ("Aaj hum tenses seekhenge!")
 *   "hindi"     → Hindi mein explanation, English grammar terms
 */
export interface StartVoiceSessionRequest {
  student_level: string;
  native_language: string;
}

/**
 * Session start hone ka response — backend se aayega
 *
 * session_id: UUID — unique session identifier
 *   Socho jaise restaurant mein table number — pata chale ki
 *   kaunse student ki kaunsi conversation chal rahi hai
 *
 * message: Emma ka greeting — "Hi! Main Emma hoon..." (language aware)
 */
export interface StartVoiceSessionResponse {
  session_id: string;
  student_level: string;
  message: string;
}

/**
 * Student ka message bhejne ka request
 *
 * session_id: Kaunsi session mein baat kar rahe ho
 * text: Student ne kya bola/likha — STT ka output ya typed text
 */
export interface TextTalkRequest {
  session_id: string;
  text: string;
}

/**
 * Ek correction ka shape — jab Emma koi mistake swarasti hai
 *
 * original:    Student ne kya bola ("I goes to school")
 * corrected:   Sahi kya hona chahiye tha ("I go to school")
 * error_type:  Error ki category ("grammar", "vocabulary", "pronunciation")
 * explanation: Emma ki samjhaaish ("'goes' third person singular ke liye hai")
 */
export interface CorrectionItem {
  original: string;
  corrected: string;
  error_type: string;
  explanation: string;
}

/**
 * Emma ka full response — ek turn ka poora data
 *
 * teacher_response: Emma ne kya bola (text)
 * follow_up:        Agla question ("Tell me more about your hobby!")
 * corrections:      Mistakes list (max 2 per turn — student overwhelm na ho)
 * audio_url:        TTS audio ka URL ("/voice/audio/abc.mp3")
 * latency:          Performance timing {"llm_ms": 700, "tts_ms": 5000, ...}
 * session_state:    Current state {"mode": "free_talk", "level": "beginner"}
 * turn_number:      Kitni baari baat ho chuki hai (1, 2, 3...)
 */
export interface TalkResponse {
  teacher_response: string;
  follow_up: string;
  corrections: CorrectionItem[];
  audio_url: string;
  latency: Record<string, number>;
  session_state: Record<string, unknown>;
  turn_number: number;
}

// ============================================================
// API Functions
// ============================================================

/**
 * Health check — server + Ollama chal raha hai ya nahi
 */
export const checkHealth = async (): Promise<HealthResponse> => {
  const response = await api.get<HealthResponse>("/health");
  return response.data;
};

/**
 * Question poocho — teacher se jawab lo
 *
 * async/await + TypeScript:
 * Promise<AskResponse> = "yeh function ek promise return karega
 * jiska result AskResponse type ka hoga"
 */
export const askQuestion = async (
  request: AskRequest,
): Promise<AskResponse> => {
  const response = await api.post<AskResponse>("/ask", request);
  return response.data;
};

/**
 * Streaming API — word by word response lo
 *
 * fetch() use kar rahe hain Axios ki jagah kyunki
 * Axios abhi ReadableStream properly support nahi karta.
 *
 * ReadableStream kya hai?
 * ──────────────────────
 * Normally: Poora data ek baar mein aata hai
 * Stream: Data chunks mein aata hai — thoda thoda
 *
 * Socho jaise nadi — paani continuously behta hai,
 * tum glass bhar ke peete jao, poori nadi drink nahi karte ek baar mein!
 */
export const askQuestionStream = async (
  request: AskRequest,
  onToken: (token: string) => void,
  onMeta: (meta: { sources: string[]; teacher: string }) => void,
  onDone: (data: { confidence: string; is_verified: boolean }) => void,
  onError: (error: string) => void,
) => {
  try {
    const response = await fetch(`${API_BASE}/ask/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });

    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    if (!response.body) throw new Error("No response body");

    // ReadableStream se data padho
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // SSE format: "data: {...}\n\n"
      const lines = buffer.split("\n\n");
      buffer = lines.pop() || ""; // Last incomplete line buffer mein rakho

      for (const line of lines) {
        const data = line.replace("data: ", "").trim();
        if (!data || data === "[DONE]") continue;

        try {
          const parsed = JSON.parse(data);

          if (parsed.type === "token") {
            onToken(parsed.token); // Har word screen pe dikhao
          } else if (parsed.type === "meta") {
            onMeta({ sources: parsed.sources, teacher: parsed.teacher });
          } else if (parsed.type === "done") {
            onDone({
              confidence: parsed.confidence,
              is_verified: parsed.is_verified,
            });
          } else if (parsed.type === "replace") {
            // Verified answer different hai — replace karo
            onToken("\n\n✏️ [Verified]: " + parsed.text);
          }
        } catch {
          // JSON parse fail — skip
        }
      }
    }
  } catch (error) {
    onError("❌ Server se connect nahi ho pa raha. Backend chal raha hai?");
  }
};

// ============================================================
// VOICE API FUNCTIONS — Emma se voice mein baat karo!
// ============================================================
//
// Voice chat ka flow:
//   1. startVoiceSession() → session_id milega
//   2. sendVoiceMessage()  → student ka text bhejo, Emma ka response lo
//   3. getAudioUrl()       → audio file ka full URL lo (TTS)
//
// Sab Axios use karte hain (auto JSON parse, timeout, error handling)

/**
 * Voice session shuru karo — Emma se naya conversation start!
 *
 * Endpoint: POST /voice/start
 *
 * Jaise class mein pehle attendance hoti hai, phir padhai —
 * waise pehle session start karo, phir baat karo.
 *
 * Session kyun chahiye?
 * ─────────────────────
 * Emma ko yaad rakhna padta hai ki pehle kya baat hui thi.
 * Bina session ke har message "naya student" lag jayega!
 * Session = Emma ki "notebook" jahan woh student ki history likhti hai.
 *
 * @param level     - Student ki level ("beginner" | "intermediate" | "advanced")
 * @param language  - Emma kis bhasha mein bolegi ("english" | "hinglish" | "hindi")
 * @returns         - { session_id, student_level, message (greeting) }
 */
export const startVoiceSession = async (
  level: string = "beginner",
  language: string = "hinglish",
): Promise<StartVoiceSessionResponse> => {
  const response = await api.post<StartVoiceSessionResponse>("/voice/start", {
    student_level: level,
    native_language: language,
  });
  return response.data;
};

/**
 * Emma se baat karo — text bhejo, response + audio lo!
 *
 * Endpoint: POST /voice/talk/text
 *
 * Yeh voice chat ka CORE function hai:
 *   Student: "I goes to school yesterday"
 *   Emma:    "Nice try! But it should be 'I went to school'..."
 *            + corrections list
 *            + audio_url (Emma ki awaaz!)
 *            + follow-up question
 *
 * Internally kya hota hai (backend mein):
 * ──────────────────────────────────────
 * 1. RAG search → relevant teaching material dhundo
 * 2. Conversation history load karo (pichli baatein)
 * 3. LLM (Groq/Ollama) → structured JSON response
 * 4. JSON parse + validate (retry if fail)
 * 5. TTS → Emma ki awaaz generate karo (edge-tts)
 * 6. Corrections track + student level adjust
 * 7. Sab log karo (JSONL)
 *
 * @param sessionId - Session ID (startVoiceSession se mila tha)
 * @param text      - Student ne kya bola/likha
 * @returns         - TalkResponse (response, corrections, audio, latency, etc.)
 */
export const sendVoiceMessage = async (
  sessionId: string,
  text: string,
): Promise<TalkResponse> => {
  const response = await api.post<TalkResponse>("/voice/talk/text", {
    session_id: sessionId,
    text: text,
  });
  return response.data;
};

/**
 * Audio file ka full URL banao — TTS audio play karne ke liye.
 *
 * Endpoint: GET /voice/audio/{filename}
 *
 * Backend audio files temporary folder mein save karta hai.
 * Frontend ko bas filename chahiye — baaki URL hum bana dete hain.
 *
 * audio_url backend se aisa aata hai: "/voice/audio/abc123.mp3"
 * Humein banana hai: "http://localhost:8000/voice/audio/abc123.mp3"
 *
 * @param audioPath - Backend se aaya path (e.g., "/voice/audio/abc.mp3")
 * @returns         - Full URL jo <audio> tag mein use ho sake
 */
export const getAudioUrl = (audioPath: string): string => {
  // Agar already full URL hai toh wahi return karo
  if (audioPath.startsWith("http")) return audioPath;
  // Warna backend base URL jod do
  return `${API_BASE}${audioPath}`;
};

export default api;
