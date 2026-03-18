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

export default api;
