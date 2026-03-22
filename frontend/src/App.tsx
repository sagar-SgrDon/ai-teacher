/**
 * App.tsx — Root Component + React Router
 *
 * React Router kya hai?
 * ─────────────────────
 * URL ke basis pe DIFFERENT pages dikhao — bina page reload kiye!
 *
 * Socho jaise TV remote:
 * Channel 1 (/) = ChatPage (text chat)
 * Channel 2 (/voice) = VoicePage (voice chat)
 * Channel badalne pe TV restart nahi hota — sirf content change hota hai!
 *
 * BrowserRouter kya hai?
 * ─────────────────────
 * React Router ka "wrapper" — poore app ko batao ki routing ON hai.
 * Bina iske <Route> aur <Link> kaam nahi karenge.
 *
 * Routes vs Route:
 * ────────────────
 * <Routes> = "switch statement" — pehla match karo
 * <Route path="/" element={<ChatPage />} /> = "/" URL pe ChatPage dikhao
 *
 * Socho jaise if-else:
 * if (url === "/") → ChatPage
 * else if (url === "/voice") → VoicePage
 */

import { BrowserRouter, Routes, Route } from "react-router-dom";
import ChatPage from "@/pages/ChatPage";
import VoicePage from "@/pages/VoicePage";

function App() {
  return (
    <div className="dark">
      <BrowserRouter>
        <Routes>
          {/* "/" = default page — text chat */}
          <Route path="/" element={<ChatPage />} />

          {/* "/voice" = voice chat page */}
          <Route path="/voice" element={<VoicePage />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
