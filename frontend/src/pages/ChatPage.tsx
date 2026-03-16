/**
 * ChatPage — Poora Chat Interface
 * 
 * Yeh "page" component hai — saare chhote components ko ek jagah jodo.
 * 
 * useEffect kya hai?
 * ──────────────────
 * "Side effects" handle karo — jaise API calls, subscriptions, DOM manipulation.
 * 
 * useEffect(() => { ... }, []) ← empty array = SIRF page load pe ek baar chale
 * useEffect(() => { ... }, [x]) ← jab "x" change ho TAB chale
 * useEffect(() => { ... })      ← har render pe chale (avoid karo!)
 * 
 * useRef for scrolling:
 * messagesEndRef = chat ke end mein ek invisible div
 * Jab naya message aaye → us div tak scroll karo = auto-scroll!
 */

import { useEffect, useRef } from 'react'
import { useChatStore } from '@/stores/chatStore'
import { checkHealth } from '@/services/api'
import Header from '@/components/Header'
import ChatMessage from '@/components/ChatMessage'
import ChatInput from '@/components/ChatInput'
import TypingIndicator from '@/components/TypingIndicator'

export default function ChatPage() {
  const { messages, isLoading, setConnected } = useChatStore()
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Page load pe health check karo
  useEffect(() => {
    const check = async () => {
      try {
        const health = await checkHealth()
        setConnected(health.status === 'healthy')
      } catch {
        setConnected(false)
      }
    }
    check()

    // Har 900 sec mein dobara check karo
    const interval = setInterval(check, 900000)
    return () => clearInterval(interval)  // Cleanup jab page band ho
  }, [setConnected])

  // Naya message aaye → auto scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  return (
    <div className="flex flex-col h-screen bg-background">
      {/* Header */}
      <Header />

      {/* Chat Area */}
      <main className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-4xl mx-auto space-y-4">
          {/* Welcome Message — jab koi message nahi hai */}
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-[60vh] text-center gap-4">
              <div className="text-5xl animate-[float_3s_ease-in-out_infinite]">🎓</div>
              <h2 className="text-2xl font-semibold">Welcome to AI Teacher!</h2>
              <p className="text-muted-foreground max-w-md">
                Choose a teacher above and ask your question below.
              </p>
              <div className="flex gap-4 mt-2">
                <div className="bg-card border border-border rounded-xl p-4 flex flex-col items-center gap-2 hover:-translate-y-1 transition-transform cursor-default">
                  <span className="text-2xl">🇬🇧</span>
                  <strong className="text-sm">English Teacher</strong>
                  <small className="text-xs text-muted-foreground">Grammar, vocabulary</small>
                </div>
                <div className="bg-card border border-border rounded-xl p-4 flex flex-col items-center gap-2 hover:-translate-y-1 transition-transform cursor-default">
                  <span className="text-2xl">💻</span>
                  <strong className="text-sm">Coding Teacher</strong>
                  <small className="text-xs text-muted-foreground">DSA, algorithms</small>
                </div>
              </div>
            </div>
          )}

          {/* Messages */}
          {messages.map((msg) => (
            <ChatMessage key={msg.id} message={msg} />
          ))}

          {/* Typing Indicator */}
          {isLoading && <TypingIndicator />}

          {/* Scroll anchor — invisible div for auto-scroll */}
          <div ref={messagesEndRef} />
        </div>
      </main>

      {/* Input */}
      <ChatInput />
    </div>
  )
}
