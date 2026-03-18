/**
 * App.tsx — Root Component
 * 
 * "dark" class body pe lagane se shadcn ke saare components 
 * automatically dark mode mein aa jaate hain!
 * 
 * Abhi simple hai — sirf ChatPage render karo.
 * Baad mein React Router add karke Topics page bhi aayega.
 */

import ChatPage from '@/pages/ChatPage'

function App() {
  return (
    <div className="dark">
      <ChatPage />
    </div>
  )
}

export default App
