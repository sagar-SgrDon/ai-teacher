/**
 * ChatInput — Message type karo aur bhejo
 * 
 * useRef kya hai?
 * ──────────────
 * DOM element ko directly pakdo (bina re-render kiye).
 * Hum textarea ke liye use kar rahe hain — auto-focus ke liye.
 * 
 * useState vs useRef:
 * useState → data change = UI re-render
 * useRef → data change = UI re-render NAHI (silent access)
 */

import { useState, useRef, useEffect } from 'react'
import { Send } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useChatStore } from '@/stores/chatStore'
import { askQuestion } from '@/services/api'

export default function ChatInput() {
  const [input, setInput] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const { teacherType, verify, isLoading, addMessage, setLoading } = useChatStore()

  // Component mount hote hi textarea pe focus
  useEffect(() => {
    textareaRef.current?.focus()
  }, [])

  // Auto-resize textarea
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value)
    const textarea = e.target
    textarea.style.height = 'auto'
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px'
  }

  // Message send karo
  const handleSend = async () => {
    const question = input.trim()
    if (!question || isLoading) return

    // 1. User message add karo
    addMessage({ text: question, type: 'user' })
    setInput('')
    if (textareaRef.current) textareaRef.current.style.height = 'auto'

    // 2. Loading ON
    setLoading(true)

    try {
      // 3. API call
      const response = await askQuestion({
        question,
        teacher_type: teacherType,
        verify,
      })

      // 4. AI message add karo
      addMessage({
        text: response.answer,
        type: 'ai',
        confidence: response.confidence,
        sources: response.sources,
        teacher: response.teacher,
        isVerified: response.is_verified,
      })
    } catch (error) {
      addMessage({
        text: '❌ Server se connect nahi ho pa raha. Kya backend chal raha hai?',
        type: 'ai',
      })
    }

    // 5. Loading OFF
    setLoading(false)
    textareaRef.current?.focus()
  }

  // Enter = send, Shift+Enter = new line
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <footer className="border-t border-border bg-card/50 backdrop-blur-sm p-4">
      <div className="flex gap-3 max-w-4xl mx-auto items-end">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          placeholder="Type your question here... (Shift+Enter for new line)"
          rows={1}
          disabled={isLoading}
          className="flex-1 resize-none bg-muted border border-border rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-ring text-foreground placeholder:text-muted-foreground disabled:opacity-50"
        />
        <Button
          onClick={handleSend}
          disabled={isLoading || !input.trim()}
          size="icon"
          className="shrink-0 rounded-xl h-10 w-10"
        >
          <Send className="w-4 h-4" />
        </Button>
      </div>
    </footer>
  )
}
