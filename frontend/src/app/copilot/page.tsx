import { ChatWindow } from '@/components/copilot/chat-window'

export default function CopilotPage() {
  return (
    <div className="flex h-full flex-col">
      <div className="flex flex-1 items-center justify-center overflow-hidden px-4">
        <div className="h-full w-full max-w-6xl">
          <ChatWindow />
        </div>
      </div>
    </div>
  )
}
