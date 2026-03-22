/**
 * VoiceHeader — Voice Chat ka Premium top bar 🎤
 *
 * Yeh ChatPage ke Header jaisa hai, par voice ke liye customized:
 * - Language selector (English / Hinglish / Hindi)
 * - Session status indicator (connected ya nahi)
 * - MODE TOGGLE: Chat ↔ Voice switch (React Router Link)
 *
 * React Router ka Link vs <a> tag:
 * ────────────────────────────────
 * <a href="/"> = POORA page reload hota hai (slow, state lost!)
 * <Link to="/"> = Sirf component change hota hai (fast, SPA magic!)
 *
 * SPA = Single Page Application
 * Page reload nahi hota — sirf content swap hota hai.
 * YouTube jaisa — video change hota hai, page nahi.
 */

import { MessageSquare, Globe, Wifi, WifiOff } from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useVoiceStore, type NativeLanguage } from "@/stores/voiceStore";

/**
 * Language options — Emma kaunsi bhasha mein bolegi
 *
 * as const kya hai?
 * ─────────────────
 * TypeScript ko bolo: "yeh array FIXED hai, change nahi hoga"
 * Isse TypeScript exact values (literals) track karta hai,
 * generic "string" type nahi.
 *
 * Bina as const: languages[0].value = string (generic)
 * With as const: languages[0].value = "english" (exact!)
 */
const LANGUAGES: { value: NativeLanguage; label: string; flag: string }[] = [
  { value: "english", label: "English", flag: "🇬🇧" },
  { value: "hinglish", label: "Hinglish", flag: "🇮🇳" },
  { value: "hindi", label: "हिंदी", flag: "🇮🇳" },
];

interface VoiceHeaderProps {
  isConnected: boolean;
}

export default function VoiceHeader({ isConnected }: VoiceHeaderProps) {
  // Zustand se data lo — language change hoga toh component re-render hoga
  const { nativeLanguage, setNativeLanguage, sessionId } = useVoiceStore();

  return (
    <header className="border-b border-border bg-card/80 backdrop-blur-md px-6 py-3">
      <div className="flex items-center justify-between max-w-4xl mx-auto">
        {/* Left — Title + Status badges */}
        <div className="flex items-center gap-3">
          <h1 className="text-xl font-bold bg-linear-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
            🎤 Voice Chat
          </h1>

          {/* Connection status badge */}
          <Badge
            variant={isConnected ? "default" : "destructive"}
            className="text-xs gap-1"
          >
            {isConnected ? (
              <Wifi className="w-3 h-3" />
            ) : (
              <WifiOff className="w-3 h-3" />
            )}
            {isConnected ? "Connected" : "Offline"}
          </Badge>

          {/* Session active badge — sirf jab session chal raha ho */}
          {sessionId && (
            <Badge
              variant="outline"
              className="text-xs text-green-400 border-green-500/30"
            >
              🟢 Session Active
            </Badge>
          )}
        </div>

        {/* Right — Language selector + Chat Mode Toggle */}
        <div className="flex items-center gap-2">
          <Globe className="w-4 h-4 text-muted-foreground" />

          {/*
           * Language toggle buttons
           *
           * .map() kya karta hai?
           * ─────────────────────
           * Array ke har item pe ek function chalao aur naya array banao.
           * LANGUAGES array ke har language ke liye ek Button render karo.
           *
           * Socho jaise assembly line:
           * Input:  [english, hinglish, hindi]
           * Output: [<Button english>, <Button hinglish>, <Button hindi>]
           */}
          {LANGUAGES.map((lang) => (
            <Button
              key={lang.value}
              variant={nativeLanguage === lang.value ? "default" : "outline"}
              size="sm"
              onClick={() => setNativeLanguage(lang.value)}
              className="text-xs gap-1"
            >
              {lang.flag} {lang.label}
            </Button>
          ))}

          {/* ── Chat Mode Toggle (NAYA!) ── */}
          {/*
           * Divider + Link to Chat Page
           *
           * Same pattern as Header.tsx mein Voice toggle —
           * consistent UX dono pages pe!
           *
           * border-l = visual separator (vertical line)
           */}
          <div className="border-l border-border pl-2 ml-1">
            <Link to="/">
              <Button
                variant="outline"
                size="sm"
                className="text-xs gap-1 border-blue-500/30 text-blue-400 hover:bg-blue-500/10 hover:text-blue-300"
              >
                <MessageSquare className="w-3 h-3" />
                💬 Chat Mode
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </header>
  );
}
