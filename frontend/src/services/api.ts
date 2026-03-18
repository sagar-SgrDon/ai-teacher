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

import axios from 'axios'

// Backend ka address — FastAPI server yahan chal raha hai
const API_BASE = 'http://localhost:8000'

// Axios instance banao — ek baar config karo, baar baar use karo
const api = axios.create({
  baseURL: API_BASE,
  timeout: 120000,  // 120 seconds max wait (LLM slow hai)
  headers: {
    'Content-Type': 'application/json',
  },
})

// ============================================================
// Types — Response ka shape define karo
// ============================================================

export interface AskRequest {
  question: string
  teacher_type: 'english' | 'coding'
  verify: boolean
}

export interface AskResponse {
  answer: string
  confidence: string
  is_verified: boolean
  sources: string[]
  teacher: string
}

export interface HealthResponse {
  status: string
  ollama: string
  teachers: string[]
}

// ============================================================
// API Functions
// ============================================================

/**
 * Health check — server + Ollama chal raha hai ya nahi
 */
export const checkHealth = async (): Promise<HealthResponse> => {
  const response = await api.get<HealthResponse>('/health')
  return response.data
}

/**
 * Question poocho — teacher se jawab lo
 * 
 * async/await + TypeScript:
 * Promise<AskResponse> = "yeh function ek promise return karega 
 * jiska result AskResponse type ka hoga"
 */
export const askQuestion = async (request: AskRequest): Promise<AskResponse> => {
  const response = await api.post<AskResponse>('/ask', request)
  return response.data
}

export default api
