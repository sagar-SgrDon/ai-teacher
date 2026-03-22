/**
 * VoicePage — Premium Voice Chat Interface 🎤✨
 *
 * Layout:
 * ┌─────────────────────────────┐
 * │ VoiceHeader (lang, nav)     │  ← glassmorphism header
 * ├─────────────────────────────┤
 * │                             │
 * │   Welcome / Messages area   │  ← gradient background
 * │   - Emma bubbles            │  ← glassmorphism cards
 * │   - Student bubbles         │
 * │   - Correction cards        │
 * │                             │
 * ├─────────────────────────────┤
 * │   VoiceMicButton (glow!)    │  ← glowing mic button
 * │   End Session               │
 * └─────────────────────────────┘
 *
 * PREMIUM DESIGN PRINCIPLES:
 * ─────────────────────────
 * 1. Gradient backgrounds (purple → blue tones)
 * 2. Glassmorphism (bg-opacity + backdrop-blur)
 * 3. Glow effects (box-shadow with color)
 * 4. Smooth animations (framer-motion)
 * 5. Visual hierarchy (important things stand out)
 *
 * FLOW:
 * ─────
 * 1. Page load → health check (server chal raha hai?)
 * 2. Welcome screen with floating Emma + "Start Session"
 * 3. Mic click → listen → STT → text → Emma response + audio
 * 4. Repeat (conversation loop!)
 * 5. "End Session" → reset
 */

import { useEffect, useRef, useState } from "react";
import { useVoiceStore } from "@/stores/voiceStore";
import { checkHealth, startVoiceSession } from "@/services/api";
import VoiceHeader from "@/components/voice/VoiceHeader";
import VoiceMessage from "@/components/voice/VoiceMessage";
import VoiceMicButton from "@/components/voice/VoiceMicButton";
import { Button } from "@/components/ui/button";
import { motion } from "framer-motion";
import { Phone, PhoneOff, Sparkles } from "lucide-react";

export default function VoicePage() {
  // ── State ──
  const [isConnected, setIsConnected] = useState(false);
  const [isStarting, setIsStarting] = useState(false);

  // Zustand store se data + actions
  const {
    sessionId,
    nativeLanguage,
    messages,
    status,
    error,
    setSessionId,
    addMessage,
    setError,
    resetSession,
  } = useVoiceStore();

  /**
   * useRef for auto-scroll
   *
   * messagesEndRef = messages ke END mein ek invisible div
   * Jab naya message aaye → us div tak scroll karo = auto-scroll!
   */
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // ── Health Check (page load pe ek baar) ──
  useEffect(() => {
    const check = async () => {
      try {
        const health = await checkHealth();
        setIsConnected(health.status === "healthy");
      } catch {
        setIsConnected(false);
      }
    };
    check();
  }, []);

  // ── Auto-scroll jab naye messages aayein ──
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, status]);

  /**
   * Session Start karo — Emma se naya conversation!
   */
  const handleStartSession = async () => {
    if (!isConnected) {
      setError("Server offline hai! Backend start karo.");
      return;
    }

    setIsStarting(true);
    setError(null);

    try {
      const response = await startVoiceSession("beginner", nativeLanguage);
      setSessionId(response.session_id);
      addMessage({ text: response.message, type: "emma" });
    } catch (err) {
      console.error("Session start error:", err);
      setError("Session start nahi ho payi. Server check karo!");
    }

    setIsStarting(false);
  };

  const handleEndSession = () => {
    resetSession();
  };

  return (
    <div className="flex flex-col h-screen bg-background relative overflow-hidden">
      {/*
       * Background gradient layers
       *
       * Multiple overlapping gradients create depth:
       * Layer 1: Purple glow (top-left)
       * Layer 2: Blue glow (bottom-right)
       * Layer 3: Pink accent (center)
       *
       * pointer-events-none = yeh sirf visual hai,
       * mouse clicks yahan se guzar jayenge (neeche ke elements ko mile)
       *
       * opacity-20 = bahut faint (subtle effect, overpowering nahi)
       */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-0 left-0 w-96 h-96 bg-purple-500/15 rounded-full blur-3xl -translate-x-1/2 -translate-y-1/2" />
        <div className="absolute bottom-0 right-0 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl translate-x-1/2 translate-y-1/2" />
        <div className="absolute top-1/2 left-1/2 w-64 h-64 bg-pink-500/5 rounded-full blur-3xl -translate-x-1/2 -translate-y-1/2" />
      </div>

      {/* Header — Language selector, navigation */}
      <VoiceHeader isConnected={isConnected} />

      {/* Main Chat Area */}
      <main className="flex-1 overflow-y-auto px-4 py-6 relative z-10">
        <div className="max-w-4xl mx-auto space-y-4">
          {/*
           * WELCOME SCREEN — jab session start nahi hua
           *
           * Premium welcome screen with:
           * - Glowing avatar card
           * - Feature highlights
           * - Animated gradient button
           */}
          {!sessionId && (
            <div className="flex flex-col items-center justify-center h-[65vh] text-center gap-8">
              {/* Emma Avatar Card — glassmorphism effect */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                className="relative"
              >
                {/* Glow ring behind avatar */}
                <div className="absolute inset-0 bg-purple-500/20 rounded-3xl blur-2xl scale-110" />

                <div className="relative bg-card/60 backdrop-blur-xl border border-border/50 rounded-3xl p-8 shadow-2xl">
                  {/* Floating emoji with glow */}
                  <motion.div
                    className="text-7xl mb-4"
                    animate={{ y: [0, -8, 0] }}
                    transition={{
                      duration: 3,
                      repeat: Infinity,
                      ease: "easeInOut",
                    }}
                  >
                    👩‍🏫
                  </motion.div>

                  <h2 className="text-2xl font-bold mb-1">
                    Meet{" "}
                    <span className="bg-linear-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                      Emma
                    </span>
                  </h2>
                  <p className="text-muted-foreground text-sm">
                    Your AI English Teacher
                  </p>
                </div>
              </motion.div>

              {/* Feature highlights */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.3, duration: 0.6 }}
                className="flex gap-3 flex-wrap justify-center max-w-lg"
              >
                {/*
                 * Feature cards — kya kya kar sakti hai Emma
                 *
                 * Glassmorphism: bg-card/40 + backdrop-blur + border-border/30
                 * = semi-transparent, blurred background, subtle border
                 * = premium glass effect! ✨
                 */}
                {[
                  { icon: "🗣️", text: "Speak naturally" },
                  { icon: "✏️", text: "Get corrections" },
                  { icon: "🎧", text: "Hear Emma talk" },
                  { icon: "🇮🇳", text: "Hinglish support" },
                ].map((feature, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.4 + i * 0.1 }}
                    className="bg-card/40 backdrop-blur-sm border border-border/30 rounded-xl px-4 py-2.5 text-xs text-muted-foreground flex items-center gap-2"
                  >
                    <span className="text-base">{feature.icon}</span>
                    {feature.text}
                  </motion.div>
                ))}
              </motion.div>

              {/* Language indicator */}
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.6 }}
                className="text-sm text-muted-foreground"
              >
                Speaking in{" "}
                <span className="text-foreground font-semibold">
                  {nativeLanguage === "hinglish"
                    ? "🇮🇳 Hinglish"
                    : nativeLanguage === "hindi"
                      ? "🇮🇳 हिंदी"
                      : "🇬🇧 English"}
                </span>
              </motion.p>

              {/* Start Session Button — gradient + glow */}
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.7 }}
              >
                <Button
                  onClick={handleStartSession}
                  disabled={isStarting || !isConnected}
                  size="lg"
                  className="gap-2 text-base px-10 py-6 rounded-2xl bg-linear-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white shadow-lg shadow-purple-500/20 hover:shadow-purple-500/40 transition-all duration-300 border-0"
                >
                  {isStarting ? (
                    <>
                      <Sparkles className="w-5 h-5 animate-spin" />
                      Starting...
                    </>
                  ) : (
                    <>
                      <Phone className="w-5 h-5" />
                      Start Session
                    </>
                  )}
                </Button>
              </motion.div>

              {/* Offline warning */}
              {!isConnected && (
                <motion.p
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="text-xs text-destructive bg-destructive/10 border border-destructive/20 rounded-xl px-4 py-2"
                >
                  ⚠️ Server offline — start backend first
                  <br />
                  uvicorn backend.app.main:app --reload --port 8000
                </motion.p>
              )}
            </div>
          )}

          {/* Messages — conversation bubbles */}
          {sessionId &&
            messages.map((msg) => <VoiceMessage key={msg.id} message={msg} />)}

          {/* Thinking indicator — jab Emma soch rahi hai */}
          {status === "thinking" && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex gap-3"
            >
              <div className="w-8 h-8 rounded-full bg-muted/50 backdrop-blur-sm flex items-center justify-center text-sm border border-border/50">
                👩‍🏫
              </div>
              <div className="bg-card/40 backdrop-blur-sm border border-border/30 rounded-2xl rounded-bl-sm px-4 py-3">
                <div className="flex gap-1.5">
                  {/*
                   * Typing dots — wave effect
                   * 3 dots, staggered delay = cascading bounce
                   */}
                  {[0, 0.15, 0.3].map((delay, i) => (
                    <motion.div
                      key={i}
                      className="w-2 h-2 bg-purple-400 rounded-full"
                      animate={{ y: [0, -6, 0] }}
                      transition={{
                        duration: 0.6,
                        delay,
                        repeat: Infinity,
                      }}
                    />
                  ))}
                </div>
              </div>
            </motion.div>
          )}

          {/* Error Message */}
          {error && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-destructive/10 backdrop-blur-sm border border-destructive/30 rounded-xl px-4 py-2 text-sm text-destructive text-center"
            >
              {error}
            </motion.div>
          )}

          {/* Scroll anchor */}
          <div ref={messagesEndRef} />
        </div>
      </main>

      {/* Bottom — Mic Button + Session Controls */}
      {sessionId && (
        <footer className="border-t border-border/50 bg-card/30 backdrop-blur-xl p-6 relative z-10">
          <div className="max-w-4xl mx-auto flex flex-col items-center gap-3">
            {/* Mic Button */}
            <VoiceMicButton />

            {/* End Session Button */}
            <Button
              variant="ghost"
              size="sm"
              onClick={handleEndSession}
              className="text-xs text-muted-foreground hover:text-destructive gap-1"
            >
              <PhoneOff className="w-3 h-3" />
              End Session
            </Button>
          </div>
        </footer>
      )}
    </div>
  );
}
