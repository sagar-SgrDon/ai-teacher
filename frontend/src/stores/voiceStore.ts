/**
 * Voice Store — Voice Chat ki Memory (Zustand)
 *
 * Zustand kya hai? (recap)
 * ────────────────────────
 * State management library — app ka "brain" jahan data store hota hai.
 * create() se store banate hain, set() se update karte hain.
 * Jab data update hota hai → UI AUTOMATICALLY re-render!
 *
 * Voice Store vs Chat Store:
 * ─────────────────────────
 * Chat Store  = text chat ke liye (streaming, sources, confidence)
 * Voice Store = voice chat ke liye (sessions, corrections, audio, status)
 *
 * Alag kyun?
 * ──────────
 * Voice chat ka flow bilkul alag hai:
 * - Session start-end concept (class jaisa — enter, learn, exit)
 * - Corrections tracking (mistakes highlight karna)
 * - Audio playback (Emma ki awaaz)
 * - Status states (idle → listening → thinking → speaking)
 *
 * Dono stores ko ek mein merge karna = "God Object" anti-pattern
 * (ek jagah pe sab daal do = messy code, hard to maintain)
 *
 * STATUS STATES kya hain?
 * ──────────────────────
 * Voice chat mein student ko har waqt pata hona chahiye ki kya ho raha hai.
 * 4 states hain:
 *
 * "idle"      → Kuch nahi ho raha, mic button ready hai
 * "listening" → Mic ON, student bol raha hai (Web Speech API)
 * "thinking"  → Emma soch rahi hai (LLM + TTS process ho raha hai)
 * "speaking"  → Emma bol rahi hai (audio play ho raha hai)
 *
 * Socho jaise traffic light:
 *   🟢 idle = green (free, kuch karo)
 *   🔴 listening = red (ruko, sun raha hai)
 *   🟡 thinking = yellow (wait karo)
 *   🔵 speaking = blue (Emma bol rahi hai)
 */

import { create } from "zustand";
import type { CorrectionItem } from "@/services/api";

// ============================================================
// Types — Voice chat ke data structures
// ============================================================

/**
 * Voice message ka shape — chat store ke Message se ALAG hai
 *
 * Kya extra hai?
 * ──────────────
 * corrections: Emma ne kaunsi mistakes pakdi (grammar, vocabulary, etc.)
 * audioUrl:    TTS audio ka path (Emma ki awaaz sunne ke liye)
 *
 * "user" messages mein corrections aur audio nahi hoti —
 * woh sirf "emma" messages mein aati hain.
 *
 * Socho jaise notebook mein:
 * - Student likhe: "I goes to school" (plain text)
 * - Teacher likhe: "It's 'I go to school'" + red pen marks (corrections!)
 */
export interface VoiceMessage {
  id: number;
  text: string;
  type: "user" | "emma";
  corrections?: CorrectionItem[];
  audioUrl?: string;
  timestamp: Date;
}

/**
 * 4 Status States — UI ka visual feedback
 *
 * Type literal union kya hai?
 * ──────────────────────────
 * "idle" | "listening" | ... = SIRF yeh 4 values allowed hain.
 * Agar koi "loading" likhe → TypeScript ERROR de dega!
 * Galti compile time pe pakad lenge, runtime pe nahi.
 */
export type VoiceStatus = "idle" | "listening" | "thinking" | "speaking";

/**
 * Native language options
 *
 * Yeh 3 languages Emma support karti hai:
 * "english"  → Pure English teaching
 * "hinglish" → Hindi-English mix (default — relatable hai!)
 * "hindi"    → Hindi mein samjhao, English terms ke saath
 */
export type NativeLanguage = "english" | "hinglish" | "hindi";

/**
 * Store ka full shape — saara data + saare actions
 *
 * interface kya hai? (recap)
 * ─────────────────────────
 * TypeScript mein interface = blueprint/contract
 * "Is store mein yeh data hoga aur yeh functions honge"
 *
 * Data vs Actions:
 * - Data = kya store hai (messages, sessionId, status)
 * - Actions = data ko CHANGE karne ke functions (addMessage, setStatus)
 */
interface VoiceState {
  // ── Data ──
  sessionId: string | null; // null = no active session
  nativeLanguage: NativeLanguage;
  status: VoiceStatus;
  messages: VoiceMessage[];
  error: string | null; // Error message (agar kuch galat ho)

  // ── Actions ──
  setSessionId: (id: string | null) => void;
  setNativeLanguage: (lang: NativeLanguage) => void;
  setStatus: (status: VoiceStatus) => void;
  setError: (error: string | null) => void;
  addMessage: (message: Omit<VoiceMessage, "id" | "timestamp">) => void;
  clearMessages: () => void;
  resetSession: () => void;
}

// ============================================================
// Store Create — Zustand magic ✨
// ============================================================

/**
 * Omit<VoiceMessage, 'id' | 'timestamp'> kya hai? (recap)
 * ──────────────────────────────────────────────────────
 * "VoiceMessage chahiye BUT id aur timestamp ke BINA"
 *
 * Kyun? id aur timestamp hum ANDAR auto-generate karte hain
 * (Date.now() se) — caller ko dene ki zaroorat nahi.
 *
 * Socho jaise form mein "Reference Number" field nahi hota —
 * woh system khud generate karta hai!
 */

export const useVoiceStore = create<VoiceState>((set) => ({
  // ── Initial State ──
  // App start hone pe yeh values hongi
  sessionId: null, // Koi session nahi abhi
  nativeLanguage: "hinglish", // Default: Hinglish (user ki preference)
  status: "idle", // Ready, kuch nahi ho raha
  messages: [], // Koi message nahi
  error: null, // Koi error nahi

  // ── Actions ──

  /**
   * Session ID set/clear karo
   * null = session end/not started
   * "abc-123" = active session
   */
  setSessionId: (id) => set({ sessionId: id }),

  /**
   * Language change karo
   * Jab student language selector mein "Hindi" select kare
   * → yeh fire hoga → next session is language mein shuru hoga
   */
  setNativeLanguage: (lang) => set({ nativeLanguage: lang }),

  /**
   * Status update karo — UI visual feedback ke liye
   * "idle" → "listening" → "thinking" → "speaking" → "idle"
   */
  setStatus: (status) => set({ status }),

  /**
   * Error set/clear karo
   * null = no error, string = error message dikhao
   */
  setError: (error) => set({ error }),

  /**
   * Naya message add karo — user ya emma ka
   *
   * Spread operator (...) kya karta hai?
   * ────────────────────────────────────
   * ...state.messages = purane saare messages COPY karo
   * { ...message, id: X, timestamp: Y } = naye message mein id aur timestamp ADD karo
   *
   * Socho jaise stack of papers:
   * ...purane papers = purane sab rakho
   * + naya paper = upar rakh do (with auto-generated ID)
   */
  addMessage: (message) =>
    set((state) => ({
      messages: [
        ...state.messages,
        {
          ...message,
          id: Date.now(), // Unique ID = current timestamp (milliseconds)
          timestamp: new Date(), // Kab bheja — for display
        },
      ],
    })),

  /**
   * Saare messages clear karo — naya session shuru karne mein useful
   */
  clearMessages: () => set({ messages: [] }),

  /**
   * Full reset — session end, messages clear, status idle
   * Jab student "End Session" kare → sab saaf!
   */
  resetSession: () =>
    set({
      sessionId: null,
      status: "idle",
      messages: [],
      error: null,
    }),
}));
