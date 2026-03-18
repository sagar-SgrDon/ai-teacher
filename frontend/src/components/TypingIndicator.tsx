/**
 * TypingIndicator — AI soch raha hai wala animation
 * 
 * motion.div se har dot ko alag alag delay mein bounce karate hain.
 * transition.repeat = Infinity → kabhi na ruke!
 */

import { motion } from 'framer-motion'

export default function TypingIndicator() {
  return (
    <div className="flex gap-3">
      <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center text-sm shrink-0 border border-border">
        🤖
      </div>
      <div className="bg-muted rounded-2xl rounded-bl-sm px-4 py-3 flex gap-1.5">
        {[0, 1, 2].map((i) => (
          <motion.div
            key={i}
            className="w-2 h-2 rounded-full bg-muted-foreground"
            animate={{ y: [0, -6, 0] }}
            transition={{
              duration: 0.8,
              repeat: Infinity,
              delay: i * 0.15,
            }}
          />
        ))}
      </div>
    </div>
  )
}
