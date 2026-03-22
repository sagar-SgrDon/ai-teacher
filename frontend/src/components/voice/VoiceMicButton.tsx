/**
 * VoiceMicButton — Continuous Voice Conversation (ChatGPT Style!) 🎤🔄
 *
 * PEHLE kaise tha (OLD — single shot):
 * ────────────────────────────────────
 * Click mic → listen → stop → Emma bole → KHATAM (dobara click karo)
 * Bahut annoying! Har baar mic click karna padta tha.
 *
 * AB kaise hai (NEW — continuous loop):
 * ─────────────────────────────────────
 * Click mic ONCE → conversation loop shuru!
 *
 *   ┌──── 🎤 Listening (student bole) ────┐
 *   │                                      │
 *   │    Student chup hua                   │
 *   ▼                                      │
 *   🤔 Thinking (Emma soch rahi hai)       │
 *   │                                      │
 *   │    Response aaya                      │
 *   ▼                                      │
 *   🔊 Speaking (Emma bol rahi hai)        │
 *   │                                      │
 *   │    Audio khatam hua                   │
 *   └──────────────────────────────────────┘
 *         ↑ LOOP! Auto-restart mic! ↑
 *
 * Click mic AGAIN → conversation STOP!
 *
 * Socho jaise phone call:
 *   - Call start karo (mic ON)
 *   - Baat karo (continuous)
 *   - Call end karo (mic OFF)
 *   - Beech mein har sentence ke liye call nahi karte!
 *
 * TECHNICAL CONCEPT: useRef for continuous mode tracking
 * ────────────────────────────────────────────────────
 * isConversationActiveRef = ref (not state!)
 *
 * Kyun ref? Kyun nahi state?
 * ─────────────────────────
 * Speech recognition ke callbacks (onresult, onend) closures hain.
 * Closure = function jo apne creation time ka data "yaad" rakhta hai.
 *
 * PROBLEM with state:
 *   const [isActive, setActive] = useState(false)
 *   recognition.onend = () => {
 *     if (isActive) startListening()  // ← STALE! Purani value!
 *   }
 *   // Jab callback run hoga, isActive ki PURANI value hogi
 *   // kyunki callback create hua tab isActive false tha
 *
 * SOLUTION with ref:
 *   const isActiveRef = useRef(false)
 *   recognition.onend = () => {
 *     if (isActiveRef.current) startListening()  // ← FRESH! Latest value!
 *   }
 *   // ref.current HAMESHA latest value deta hai
 *   // kyunki ref ek object hai, .current property change hoti hai
 *
 * Socho: state = photocopy (purani), ref = original document (hamesha updated)
 */

import { useState, useRef, useCallback } from "react";
import { Mic, MicOff, Volume2, Loader2, Send, Keyboard } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { useVoiceStore } from "@/stores/voiceStore";
import { sendVoiceMessage, getAudioUrl } from "@/services/api";

// TypeScript — browser mein SpeechRecognition ka type batao
declare global {
  interface Window {
    webkitSpeechRecognition: new () => SpeechRecognition;
  }
}

export default function VoiceMicButton() {
  // ── State ──
  const [textInput, setTextInput] = useState("");
  const [showTextInput, setShowTextInput] = useState(false);

  /**
   * Refs — mutable values, re-render nahi karte
   *
   * isConversationActiveRef = CONTINUOUS MODE on/off
   *   true = loop chal raha hai (auto-restart mic after Emma speaks)
   *   false = loop band, idle pe jao
   *
   * recognitionRef = current SpeechRecognition object
   *   .stop() call karne ke liye chahiye
   *
   * audioRef = current Audio element
   *   .pause() karne ke liye chahiye (emergency stop)
   *
   * isProcessingRef = kya abhi message process ho raha hai?
   *   onend mein check karo: agar processing hai toh mic restart mat karo
   *   (pehle Emma bole, phir mic restart hoga)
   */
  const isConversationActiveRef = useRef(false);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const isProcessingRef = useRef(false);
  const silenceTimerRef = useRef<number | null>(null);

  // Zustand store
  const { sessionId, status, setStatus, addMessage, setError } =
    useVoiceStore();

  // Browser speech support check
  const isSpeechSupported =
    "webkitSpeechRecognition" in window || "SpeechRecognition" in window;

  /**
   * startListening() — Mic ON karo (ek round ke liye)
   *
   * Yeh function LOOP ka ek iteration hai:
   * 1. SpeechRecognition object banao
   * 2. Mic ON karo
   * 3. Student bole → onresult fire → processMessage()
   * 4. Student chup ho → onend fire → (agar loop active → yeh function PHIR call)
   *
   * Kyun baar baar naya recognition object?
   * ──────────────────────────────────────
   * Web Speech API ki limitation: ek recognition object SIRF ek baar use hota hai.
   * .start() ke baad .stop() hone pe wahi object se dobara .start() nahi hota
   * (ya inconsistent hota hai across browsers).
   * Solution: har round mein NAYA object banao!
   *
   * Socho jaise disposable camera — ek baar use karo, phir nayi lo.
   */
  const startListening = useCallback(() => {
    // Safety checks
    if (!isSpeechSupported || !sessionId) return;

    // Purana recognition cleanup
    if (recognitionRef.current) {
      try {
        recognitionRef.current.abort();
      } catch {
        // Ignore — already stopped
      }
    }

    const SpeechRecognitionAPI =
      window.webkitSpeechRecognition || window.SpeechRecognition;
    const recognition = new SpeechRecognitionAPI();

    // Settings
    recognition.lang = "en-IN"; // Indian English accent support
    recognition.interimResults = false; // Sirf final result
    recognition.continuous = false; // Ek utterance ke baad auto-stop

    /**
     * onresult — Student ne kuch bola! 🎉
     *
     * Yahan se processMessage() call hoga.
     * isProcessingRef = true set karo taaki onend mein
     * mic dobara start na ho (pehle Emma bole!)
     */

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      const transcript = event.results[0][0].transcript;
      if (!transcript) return;

      if (silenceTimerRef.current) {
        clearTimeout(silenceTimerRef.current);
      }

      silenceTimerRef.current = window.setTimeout(() => {
        isProcessingRef.current = true;
        processMessage(transcript);
      }, 2000);
    }; /**
     * onend — Recognition band ho gaya (natural end)
     *
     * CONTINUOUS MODE LOGIC:
     * ─────────────────────
     * 1. Agar processing ho raha hai (isProcessingRef = true):
     *    → Kuch mat karo, processMessage handle karega restart
     *
     * 2. Agar conversation active hai AUR processing nahi:
     *    → Student ne kuch nahi bola (silence/no-speech)
     *    → Mic DOBARA start karo (loop continue!)
     *
     * 3. Agar conversation active nahi:
     *    → Idle pe jao (user ne manually band kiya)
     *
     * Socho jaise teacher class mein:
     * - Student chup hai? → "Bol beta..." (mic restart)
     * - Student kuch bola? → "Sahi hai!" (process karo, phir mic restart)
     * - Class khatam? → "Bye!" (stop)
     */
    recognition.onend = () => {
      recognitionRef.current = null;

      // Case 1: Processing — processMessage will handle restart
      if (isProcessingRef.current) return;

      // Case 2: Still in conversation — restart (student was silent)
      if (isConversationActiveRef.current) {
        // Small delay to avoid rapid restarts
        setTimeout(() => {
          if (isConversationActiveRef.current) {
            startListening();
          }
        }, 300);
        return;
      }

      // Case 3: Conversation stopped — go idle
      setStatus("idle");
    };

    /**
     * onerror — Kuch galat hua
     *
     * "no-speech" = student ne kuch nahi bola — NORMAL hai!
     *   → Agar loop active → restart (keep listening)
     *
     * "not-allowed" = mic permission denied — FATAL
     *   → Loop band karo, text input dikhao
     *
     * Other errors → log karo, restart try karo
     */
    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      console.error("Speech error:", event.error);

      if (event.error === "aborted") {
        return; // 👈 ignore completely
      }

      if (event.error === "not-allowed") {
        // Fatal — mic permission nahi hai
        setError("Mic permission denied! Browser settings mein allow karo.");
        setShowTextInput(true);
        stopConversation();
        return;
      }

      if (event.error === "no-speech") {
        // Normal — student chup tha, restart karo
        // onend will handle restart via setTimeout
        return;
      }

      // Other errors — try to continue if conversation active
      if (!isConversationActiveRef.current) {
        setStatus("idle");
      }
    };

    // Sab set — MIC ON! 🎤
    recognitionRef.current = recognition;
    setStatus("listening");
    recognition.start();
  }, [isSpeechSupported, sessionId, setStatus, setError]);

  /**
   * processMessage() — Student ka message bhejo, Emma ka response lo
   *
   * CONTINUOUS MODE mein special:
   * ────────────────────────────
   * Jab Emma ka audio khatam ho (audio.onended):
   *   → isProcessingRef = false
   *   → startListening() AUTOMATICALLY call ho
   *   → Mic phir ON! Student dobara bol sake!
   *
   * Yeh hai LOOP ka secret sauce:
   *   listening → process → speak → listening → process → speak → ...
   */
  const processMessage = useCallback(
    async (text: string) => {
      if (!sessionId || !text.trim()) {
        isProcessingRef.current = false;
        // Restart listening if conversation active
        if (isConversationActiveRef.current) {
          startListening();
        }
        return;
      }

      // 1. Student ka message dikhao
      addMessage({ text: text.trim(), type: "user" });

      // 2. Status: thinking
      setStatus("thinking");

      try {
        // 3. Backend se Emma ka response lo
        const response = await sendVoiceMessage(sessionId, text.trim());

        // 4. Emma ka message add karo
        addMessage({
          text:
            response.teacher_response +
            (response.follow_up ? `\n\n${response.follow_up}` : ""),
          type: "emma",
          corrections: response.corrections,
          audioUrl: response.audio_url || undefined,
        });

        // 5. Audio play karo
        if (response.audio_url) {
          setStatus("speaking");
          const audio = new Audio(getAudioUrl(response.audio_url));
          audioRef.current = audio;

          /**
           * audio.onended — Emma bol chuki! Ab kya?
           *
           * CONTINUOUS MODE:
           *   isConversationActiveRef.current === true
           *   → isProcessingRef = false
           *   → startListening() → mic phir ON!
           *   → Student bole → cycle continue!
           *
           * STOPPED:
           *   isConversationActiveRef.current === false
           *   → idle pe jao
           */
          audio.onended = () => {
            audioRef.current = null;
            isProcessingRef.current = false;

            if (isConversationActiveRef.current) {
              // LOOP! Emma bol chuki → mic phir ON!
              startListening();
            } else {
              setStatus("idle");
            }
          };

          audio.onerror = () => {
            audioRef.current = null;
            isProcessingRef.current = false;

            if (isConversationActiveRef.current) {
              startListening();
            } else {
              setStatus("idle");
            }
          };

          await audio.play().catch(() => {
            isProcessingRef.current = false;
            if (isConversationActiveRef.current) {
              startListening();
            } else {
              setStatus("idle");
            }
          });
        } else {
          // No audio — directly restart listening or go idle
          isProcessingRef.current = false;

          if (isConversationActiveRef.current) {
            startListening();
          } else {
            setStatus("idle");
          }
        }
      } catch (err) {
        console.error("Voice message error:", err);
        setError("Emma se baat nahi ho payi. Server check karo!");
        isProcessingRef.current = false;

        if (isConversationActiveRef.current) {
          // Error pe bhi restart — resilient conversation!
          setTimeout(() => {
            if (isConversationActiveRef.current) {
              startListening();
            }
          }, 1000);
        } else {
          setStatus("idle");
        }
      }
    },
    [sessionId, addMessage, setStatus, setError, startListening],
  );

  /**
   * stopConversation() — Conversation loop BAND karo
   *
   * Sab kuch clean up:
   * 1. Loop flag OFF
   * 2. Recognition stop
   * 3. Audio stop
   * 4. Status → idle
   */
  const stopConversation = useCallback(() => {
    isConversationActiveRef.current = false;
    isProcessingRef.current = false;

    // Recognition band karo
    if (recognitionRef.current) {
      try {
        recognitionRef.current.abort();
      } catch {
        // Ignore
      }
      recognitionRef.current = null;
    }

    // Audio band karo
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }

    setStatus("idle");
  }, [setStatus]);

  /**
   * handleMicClick() — MIC BUTTON TOGGLE
   *
   * Click 1: Conversation START (loop begins!)
   *   → isConversationActiveRef = true
   *   → startListening()
   *   → Ab loop chalega: listen → think → speak → listen → ...
   *
   * Click 2: Conversation STOP (loop ends!)
   *   → stopConversation()
   *   → Sab band, idle pe wapas
   *
   * Socho jaise phone call:
   *   Pehla click = call start (📞 ring ring)
   *   Doosra click = call end (📵 bye bye)
   */
  const handleMicClick = () => {
    // Session check
    if (!sessionId) {
      setError("Pehle session start karo!");
      return;
    }

    // Speech support check
    if (!isSpeechSupported) {
      setShowTextInput(true);
      return;
    }

    // TOGGLE: agar conversation chal raha hai → band karo
    if (isConversationActiveRef.current) {
      stopConversation();
      return;
    }

    // START: conversation loop shuru!
    isConversationActiveRef.current = true;
    startListening();
  };

  /**
   * Text fallback — jab mic nahi chale
   */
  const handleTextSend = () => {
    if (textInput.trim()) {
      isProcessingRef.current = true;
      processMessage(textInput.trim());
      setTextInput("");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleTextSend();
    }
  };

  const isDisabled = !sessionId;
  const isInConversation = status !== "idle" || isConversationActiveRef.current;
  const isBusy = status === "thinking" || status === "speaking";

  return (
    <div className="flex flex-col items-center gap-4 w-full">
      {/* MIC BUTTON AREA */}
      <div className="relative flex items-center justify-center">
        {/* Pulse rings — listening state */}
        <AnimatePresence>
          {status === "listening" && (
            <>
              {[0, 0.3, 0.6].map((delay, i) => (
                <motion.div
                  key={`ring-${i}`}
                  className="absolute w-20 h-20 rounded-full border-2 border-red-400/60"
                  initial={{ scale: 1, opacity: 0.5 }}
                  animate={{ scale: 2.5, opacity: 0 }}
                  exit={{ opacity: 0 }}
                  transition={{
                    duration: 1.5,
                    delay,
                    repeat: Infinity,
                    ease: "easeOut",
                  }}
                />
              ))}
            </>
          )}
        </AnimatePresence>

        {/* State-based glow effects */}
        {status === "idle" && !isDisabled && (
          <div className="absolute w-20 h-20 bg-purple-500/20 rounded-full blur-xl" />
        )}
        {status === "speaking" && (
          <motion.div
            className="absolute w-20 h-20 bg-blue-500/30 rounded-full blur-xl"
            animate={{ scale: [1, 1.3, 1] }}
            transition={{ duration: 1.5, repeat: Infinity }}
          />
        )}
        {status === "thinking" && (
          <motion.div
            className="absolute w-20 h-20 bg-purple-500/20 rounded-full blur-xl"
            animate={{ scale: [1, 1.2, 1], opacity: [0.3, 0.6, 0.3] }}
            transition={{ duration: 2, repeat: Infinity }}
          />
        )}

        {/* MAIN MIC BUTTON */}
        <motion.button
          onClick={handleMicClick}
          disabled={isDisabled}
          whileTap={{ scale: 0.92 }}
          whileHover={{ scale: isDisabled ? 1 : 1.08 }}
          className={`
            relative z-10 w-20 h-20 rounded-full flex items-center justify-center
            transition-all duration-300 shadow-lg cursor-pointer
            ${
              isDisabled
                ? "bg-muted/50 text-muted-foreground cursor-not-allowed opacity-40"
                : status === "listening"
                  ? "bg-red-500 text-white shadow-red-500/40 shadow-2xl"
                  : status === "thinking"
                    ? "bg-card/60 backdrop-blur-sm text-purple-400 border border-purple-500/30"
                    : status === "speaking"
                      ? "bg-card/60 backdrop-blur-sm text-blue-400 border border-blue-500/30"
                      : "bg-linear-to-br from-purple-500 to-pink-500 text-white shadow-purple-500/30 shadow-xl hover:shadow-purple-500/50 hover:shadow-2xl"
            }
          `}
        >
          {/*
           * Icon changes based on status:
           * idle      → Mic (ready to start)
           * listening → MicOff (click to STOP conversation)
           * thinking  → Loader spinner
           * speaking  → Volume icon
           *
           * NOTE: thinking/speaking pe bhi MicOff icon dikhao
           * kyunki user kisi bhi waqt stop kar sakta hai!
           */}
          {status === "thinking" ? (
            <Loader2 className="w-7 h-7 animate-spin" />
          ) : status === "speaking" ? (
            <Volume2 className="w-7 h-7" />
          ) : status === "listening" ? (
            <MicOff className="w-7 h-7" />
          ) : (
            <Mic className="w-7 h-7" />
          )}
        </motion.button>
      </div>

      {/* Status Text */}
      <motion.p
        key={status}
        initial={{ opacity: 0, y: 5 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-xs text-muted-foreground font-medium"
      >
        {isDisabled
          ? "Start a session first"
          : status === "listening"
            ? "🔴 Listening... (click mic to end)"
            : status === "thinking"
              ? "✨ Emma is thinking..."
              : status === "speaking"
                ? "🔊 Emma is speaking..."
                : "Click mic to start conversation"}
      </motion.p>

      {/* "or type" toggle — idle mein dikhao */}
      {sessionId &&
        !showTextInput &&
        isSpeechSupported &&
        status === "idle" && (
          <button
            onClick={() => setShowTextInput(true)}
            className="text-xs text-muted-foreground/60 hover:text-muted-foreground flex items-center gap-1 transition-colors"
          >
            <Keyboard className="w-3 h-3" />
            or type instead
          </button>
        )}

      {/* Text Input Fallback */}
      {(showTextInput || !isSpeechSupported) && sessionId && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex gap-2 w-full max-w-md"
        >
          <input
            type="text"
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your message..."
            disabled={isBusy}
            autoFocus
            className="flex-1 bg-card/40 backdrop-blur-sm border border-border/50 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500/50 text-foreground placeholder:text-muted-foreground disabled:opacity-50"
          />
          <Button
            onClick={handleTextSend}
            disabled={!textInput.trim() || isBusy}
            size="icon"
            className="rounded-xl h-10 w-10 shrink-0 bg-linear-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white border-0"
          >
            <Send className="w-4 h-4" />
          </Button>
        </motion.div>
      )}
    </div>
  );
}
