'use client'

import { ChatWindow } from '@/components/copilot/chat-window'
import { ChatSidebar } from '@/components/copilot/chat-sidebar'
import { useState } from 'react'
import { ChevronRight } from 'lucide-react'
import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'

export default function CopilotPage() {
  const [sidebarOpen, setSidebarOpen] = useState(true)

  return (
    <div className="flex h-full w-full bg-bg-primary">
      {/* Sidebar */}
      <motion.div
        initial={false}
        animate={{ width: sidebarOpen ? 256 : 0 }}
        transition={{ duration: 0.3, ease: 'easeInOut' }}
        className="overflow-hidden flex-shrink-0"
      >
        <ChatSidebar />
      </motion.div>

      {/* Main Area */}
      <div className="relative flex flex-1 flex-col">
        {/* Toggle Button */}
        <motion.button
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          onClick={() => setSidebarOpen(!sidebarOpen)}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.95 }}
          className="absolute left-4 top-4 z-30 flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-r from-cyan-600 to-blue-600 shadow-lg transition-all duration-200 hover:from-cyan-500 hover:to-blue-500 hover:shadow-cyan-500/50"
          title={sidebarOpen ? "Hide chat history" : "Show chat history"}
        >
          <ChevronRight className={cn("h-5 w-5 text-white transition-transform", sidebarOpen && "rotate-180")} />
        </motion.button>

        {/* Chat Window - Full Size */}
        <ChatWindow />
      </div>
    </div>
  )
}
