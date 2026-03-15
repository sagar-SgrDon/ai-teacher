// App.tsx mein example
import { Button } from '@/components/ui/button'

function App() {
  return (
    <div className="dark min-h-screen bg-background text-foreground flex items-center justify-center gap-4">
      <Button>Default Button</Button>
      <Button variant="outline">Outline</Button>
      <Button variant="destructive">Delete</Button>
    </div>
  )
}

export default App
