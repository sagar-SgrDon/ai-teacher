/**
 * VoiceMessage — Premium Voice chat message bubble 🎨
 *
 * ChatMessage se kaise alag hai?
 * ─────────────────────────────
 * ChatMessage = simple text bubble (confidence, sources)
 * VoiceMessage = voice-specific bubble:
 *   - Corrections: mistakes highlight (original → corrected)
 *   - Audio Replay: Emma ki awaaz phir se sunne ka button (🔊)
 *   - Glassmorphism: semi-transparent, blurred background = premium feel
 *
 * Framer Motion kya hai? (recap)
 * ─────────────────────────────
 * Animation library — CSS animations ke bajaye React-friendly API.
 * motion.div = div with superpowers (animate on mount, exit, etc.)
 */

import { Volume2 } from "lucide-react";
import { motion } from "framer-motion";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { VoiceMessage as VoiceMessageType } from "@/stores/voiceStore";
import { getAudioUrl } from "@/services/api";

interface VoiceMessageProps {
  message: VoiceMessageType;
}

/**
 * Error type ke liye color mapping
 *
 * Record<string, string> kya hai?
 * ───────────────────────────────
 * TypeScript mein object type define karne ka short way
 * "Key string hai, value bhi string hai"
 */
const ERROR_COLORS: Record<string, string> = {
  grammar: "border-red-500/50 text-red-400",
  vocabulary: "border-yellow-500/50 text-yellow-400",
  pronunciation: "border-blue-500/50 text-blue-400",
  tense: "border-orange-500/50 text-orange-400",
  article: "border-pink-500/50 text-pink-400",
};

export default function VoiceMessage({ message }: VoiceMessageProps) {
  const isUser = message.type === "user";

  /**
   * Audio play karo — Emma ki awaaz sunao
   * new Audio(url) = browser ka built-in audio player
   */
  const playAudio = () => {
    if (message.audioUrl) {
      const audio = new Audio(getAudioUrl(message.audioUrl));
      audio.play().catch((err) => console.error("Audio play failed:", err));
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`flex gap-3 ${isUser ? "flex-row-reverse" : "flex-row"}`}
    >
      {/* Avatar — Student ya Emma */}
      <div
        className={`w-9 h-9 rounded-full flex items-center justify-center text-sm shrink-0 border ${
          isUser
            ? "bg-purple-500/20 border-purple-500/30"
            : "bg-card/60 backdrop-blur-sm border-border/50"
        }`}
      >
        {isUser ? "👤" : "👩‍🏫"}
      </div>

      {/* Message Content */}
      <div
        className={`flex flex-col gap-1.5 max-w-[80%] ${
          isUser ? "items-end" : "items-start"
        }`}
      >
        {/* Text Bubble — glassmorphism for Emma, solid for user */}
        <div
          className={`px-4 py-2.5 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
            isUser
              ? "bg-linear-to-r from-purple-500 to-pink-500 text-white rounded-br-sm shadow-lg shadow-purple-500/10"
              : "bg-card/50 backdrop-blur-sm border border-border/30 text-foreground rounded-bl-sm"
          }`}
        >
          {message.text}
        </div>

        {/* Audio Replay Button — sirf Emma messages ke liye */}
        {!isUser && message.audioUrl && (
          <Button
            variant="ghost"
            size="sm"
            onClick={playAudio}
            className="text-xs gap-1 text-purple-400 hover:text-purple-300 hover:bg-purple-500/10 h-7 rounded-lg"
          >
            <Volume2 className="w-3 h-3" />
            Replay Audio
          </Button>
        )}

        {/*
         * Corrections Section — Emma ne kaunsi mistakes pakdi
         *
         * Har correction ke liye ek card:
         * ┌────────────────────────────────────┐
         * │ ❌ "I goes" → ✅ "I go"           │
         * │ 📝 grammar                        │
         * │ 'goes' third person singular...    │
         * └────────────────────────────────────┘
         */}
        {!isUser &&
          message.corrections &&
          message.corrections.length > 0 && (
            <div className="flex flex-col gap-1.5 w-full">
              {message.corrections.map((correction, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.2 + index * 0.1 }}
                  className="bg-card/40 backdrop-blur-sm border border-border/30 rounded-xl px-3 py-2.5 text-xs"
                >
                  {/* Original → Corrected */}
                  <div className="flex items-center gap-2 mb-1.5">
                    <span className="text-red-400 line-through">
                      {correction.original}
                    </span>
                    <span className="text-muted-foreground">→</span>
                    <span className="text-green-400 font-medium">
                      {correction.corrected}
                    </span>
                  </div>

                  {/* Error Type Badge + Explanation */}
                  <div className="flex items-center gap-2">
                    <Badge
                      variant="outline"
                      className={`text-[10px] ${
                        ERROR_COLORS[correction.error_type] ||
                        "border-muted-foreground/30 text-muted-foreground"
                      }`}
                    >
                      📝 {correction.error_type}
                    </Badge>
                    <span className="text-muted-foreground">
                      {correction.explanation}
                    </span>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
      </div>
    </motion.div>
  );
}
