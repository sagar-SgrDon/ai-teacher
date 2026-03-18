/**
 * Chat Store — App ki Memory (Zustand)
 *
 * Zustand kya hai?
 * ────────────────
 * State management library — app ka "brain" jahan sab data store hota hai.
 *
 * Redux mein 100+ lines ka boilerplate likhna padta tha.
 * Zustand mein? Bas 20 lines!
 *
 * create() ek store banata hai.
 * set() se data update karte ho.
 * Jab data update hota hai → UI AUTOMATICALLY re-render hota hai!
 *
 * Socho jaise ek whiteboard — jab kuch likhte ho,
 * sab log dekhne waale ko TURANT dikhta hai.
 */

import { create } from "zustand";

// ============================================================
// Types
// ============================================================

export interface Message {
  id: number;
  text: string;
  type: "user" | "ai";
  confidence?: string;
  sources?: string[];
  teacher?: string;
  isVerified?: boolean;
  timestamp: Date;
}

export type TeacherType = "english" | "coding";

interface ChatState {
  // Data
  messages: Message[];
  teacherType: TeacherType;
  verify: boolean;
  isLoading: boolean;
  isConnected: boolean;

  // Actions — data change karne ke functions
  addMessage: (message: Omit<Message, "id" | "timestamp">) => void;
  setTeacherType: (type: TeacherType) => void;
  setVerify: (verify: boolean) => void;
  setLoading: (loading: boolean) => void;
  setConnected: (connected: boolean) => void;
  clearMessages: () => void;
  updateLastAiMessage: (text: string) => void;
}

// ============================================================
// Store Create — Zustand magic ✨
// ============================================================

/**
 * Omit<Message, 'id' | 'timestamp'> kya hai?
 * ──────────────────────────────────────────
 * TypeScript utility type — Message type se 'id' aur 'timestamp'
 * fields HATAO. Kyunki yeh fields hum ANDAR auto-generate karte hain,
 * user ko dene ki zaroorat nahi.
 *
 * Socho: "Mujhe Message chahiye BUT id aur timestamp ke BINA"
 */

export const useChatStore = create<ChatState>((set) => ({
  // Initial state — app start hone pe yeh values hongi
  messages: [],
  teacherType: "english",
  verify: false,
  isLoading: false,
  isConnected: false,

  // Actions
  addMessage: (message) =>
    set((state) => ({
      messages: [
        ...state.messages, // Purane saare messages rakho (spread operator)
        {
          ...message, // Naye message ka data
          id: Date.now(), // Unique ID = current timestamp (milliseconds)
          timestamp: new Date(), // Kab bheja
        },
      ],
    })),

  setTeacherType: (type) => set({ teacherType: type }),
  setVerify: (verify) => set({ verify }),
  setLoading: (loading) => set({ isLoading: loading }),
  setConnected: (connected) => set({ isConnected: connected }),
  clearMessages: () => set({ messages: [] }),
  updateLastAiMessage: (text) =>
    set((state) => {
      const messages = [...state.messages];
      const lastIndex = messages.length - 1;
      if (lastIndex >= 0 && messages[lastIndex].type === "ai") {
        messages[lastIndex] = {
          ...messages[lastIndex],
          text: messages[lastIndex].text + text,
        };
      }
      return { messages };
    }),
}));
