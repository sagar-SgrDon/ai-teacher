/**
 * Header Component — App ka top bar
 * 
 * React mein component = ek function jo HTML return kare.
 * Props = component ko BAHAR se data dena (function ke arguments jaisa)
 * 
 * Hum yahan Zustand store se directly data le rahe hain —
 * props ki zaroorat nahi! Zustand ka hook use karo, data aa jayega.
 */

import { Monitor, Wifi, WifiOff } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { useChatStore } from '@/stores/chatStore'

export default function Header() {
  // Zustand store se data lo — jab yeh change hoga, component APNE AAP re-render hoga
  const { teacherType, setTeacherType, verify, setVerify, isConnected } = useChatStore()

  return (
    <header className="border-b border-border bg-card/50 backdrop-blur-sm px-6 py-3">
      <div className="flex items-center justify-between max-w-4xl mx-auto">
        
        {/* Left side — Logo + Status */}
        <div className="flex items-center gap-3">
          <h1 className="text-xl font-bold bg-linear-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
            🎓 AI Teacher
          </h1>
          <Badge variant={isConnected ? 'default' : 'destructive'} className="text-xs gap-1">
            {isConnected ? <Wifi className="w-3 h-3" /> : <WifiOff className="w-3 h-3" />}
            {isConnected ? 'Connected' : 'Offline'}
          </Badge>
        </div>

        {/* Right side — Teacher selector + Verify */}
        <div className="flex items-center gap-2">
          {/* Teacher Toggle Buttons */}
          <Button
            variant={teacherType === 'english' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setTeacherType('english')}
            className="text-xs"
          >
            🇬🇧 English
          </Button>
          <Button
            variant={teacherType === 'coding' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setTeacherType('coding')}
            className="text-xs"
          >
            💻 Coding
          </Button>

          {/* Verify Toggle */}
          <Button
            variant={verify ? 'default' : 'outline'}
            size="sm"
            onClick={() => setVerify(!verify)}
            className="text-xs gap-1"
          >
            <Monitor className="w-3 h-3" />
            {verify ? '✓ Verify ON' : 'Verify OFF'}
          </Button>
        </div>
      </div>
    </header>
  )
}
