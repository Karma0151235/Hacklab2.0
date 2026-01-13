import { ChatWindow } from '@/components/copilot/chat-window'

export default function CopilotPage() {
  return (
    <div className="flex h-screen flex-col bg-gradient-to-br from-bg-primary via-bg-secondary to-bg-primary">
      {/* Page Header */}
      <div className="border-b border-border-accent/20 bg-gradient-to-br from-bg-tertiary to-bg-secondary px-8 py-6">
        <div className="mx-auto max-w-7xl">
          <div className="mb-2 flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent-primary/10">
              <svg
                className="h-6 w-6 text-accent-primary"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                />
              </svg>
            </div>
            <h1 className="font-sans text-3xl font-bold text-text-primary">
              AI Copilot
            </h1>
          </div>
          <p className="font-sans text-base text-text-secondary">
            Your intelligent assistant for financial intelligence and compliance
            monitoring
          </p>
        </div>
      </div>

      {/* Chat Window */}
      <div className="flex-1 overflow-hidden">
        <ChatWindow />
      </div>
    </div>
  )
}
