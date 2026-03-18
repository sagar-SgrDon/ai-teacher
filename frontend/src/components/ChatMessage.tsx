/**
 * ChatMessage Component — Ek message bubble
 * 
 * Props kya hai?
 * ──────────────
 * Component ko BAHAR se data dene ka tarika.
 * Socho function ke arguments jaisa:
 * 
 * function greet(name) ← name is a prop
 * <ChatMessage message={...} /> ← message is a prop
 * 
 * interface = props ka "blueprint" — TypeScript ko batao 
 * ki is component ko kya data chahiye
 */

import { Badge } from '@/components/ui/badge'
import { type Message } from '@/stores/chatStore'
import { motion } from 'framer-motion'

interface ChatMessageProps {
  message: Message
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.type === 'user'

  return (
    // motion.div = Framer Motion ka div — animations built-in!
    // initial = starting state (pehle invisible + neeche)
    // animate = final state (visible + upar aa jaye)
    // transition = kitni der mein animation ho
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
    >
      {/* Avatar */}
      <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center text-sm shrink-0 border border-border">
        {isUser ? '👤' : '🤖'}
      </div>

      {/* Message Content */}
      <div className={`flex flex-col gap-1.5 max-w-[80%] ${isUser ? 'items-end' : 'items-start'}`}>
        {/* Bubble */}
        <div
          className={`px-4 py-2.5 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
            isUser
              ? 'bg-primary text-primary-foreground rounded-br-sm'
              : 'bg-muted text-foreground rounded-bl-sm'
          }`}
        >
          {message.text}
        </div>

        {/* Metadata — sirf AI messages ke liye */}
        {!isUser && message.confidence && (
          <div className="flex flex-wrap gap-1.5">
            {/* Confidence Badge */}
            <Badge
              variant="outline"
              className={`text-[10px] ${
                message.confidence === 'high'
                  ? 'border-green-500/50 text-green-400'
                  : message.confidence === 'medium'
                  ? 'border-yellow-500/50 text-yellow-400'
                  : message.confidence === 'low'
                  ? 'border-red-500/50 text-red-400'
                  : 'border-muted-foreground/30 text-muted-foreground'
              }`}
            >
              {message.confidence === 'high' ? '✅' : message.confidence === 'medium' ? '⚠️' : message.confidence === 'low' ? '❌' : '❔'}{' '}
              {message.confidence}
            </Badge>

            {/* Verified Badge */}
            {message.isVerified && (
              <Badge variant="outline" className="text-[10px] border-green-500/50 text-green-400">
                ✓ Verified
              </Badge>
            )}

            {/* Source Tags */}
            {message.sources?.map((source, i) => (
              <Badge key={i} variant="outline" className="text-[10px] border-purple-500/30 text-purple-400">
                📚 {source}
              </Badge>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  )
}
