"use client"

import { Bot, User, Copy, Check, FileText, ChevronDown, ChevronUp } from 'lucide-react'
import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'
import { CopilotAnswer } from '@/lib/types/api'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

// Play pop sound
const playPopSound = () => {
  try {
    const audio = new Audio('/sounds/pop.wav')
    audio.volume = 0.3
    audio.play().catch(() => {})
  } catch {}
}

interface MessageBubbleProps {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  copilotAnswer?: CopilotAnswer
  className?: string
}

export function MessageBubble({
  role,
  content,
  copilotAnswer,
  className,
}: MessageBubbleProps) {
  const [copied, setCopied] = useState(false)
  const [showSources, setShowSources] = useState(false)
  const isUser = role === 'user'

  // Play pop sound on mount (new message)
  useEffect(() => {
    if (!isUser) {
      playPopSound()
    }
  }, [])

  const handleCopy = () => {
    navigator.clipboard.writeText(content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  // Clean up answer text
  let displayContent = content
  if (content.includes('================ ANSWER ================')) {
    const parts = content.split('================ ANSWER ================')
    if (parts.length > 1) {
      let answerPart = parts[1]
      if (answerPart.includes('================ AGENTS USED ================')) {
        answerPart = answerPart.split('================ AGENTS USED ================')[0]
      }
      displayContent = answerPart.trim()
    }
  }

  const citations = copilotAnswer?.citations || []

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.2, ease: 'easeOut' }}
      className={cn('flex gap-3', isUser ? 'flex-row-reverse' : '', className)}
    >
      {/* Avatar */}
      <div className={cn(
        'flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full',
        isUser ? 'bg-cyan-600' : 'bg-gray-700'
      )}>
        {isUser ? (
          <User className="h-4 w-4 text-white" />
        ) : (
          <Bot className="h-4 w-4 text-cyan-400" />
        )}
      </div>

      {/* Content */}
      <div className={cn('group max-w-[85%] relative', isUser ? 'text-right' : '')}>
        {/* Role label */}
        <div className={cn(
          'mb-1 text-xs font-medium',
          isUser ? 'text-cyan-400' : 'text-gray-400'
        )}>
          {isUser ? 'You' : 'FinIntel'}
        </div>

        {/* Message */}
        <div className={cn(
          'rounded-2xl px-4 text-sm',
          isUser 
            ? 'bg-cyan-600 text-white py-2' 
            : 'bg-gray-800 text-gray-100 py-3'
        )}>
          {isUser ? (
            <p className="whitespace-pre-wrap">{content}</p>
          ) : (
            <div className="prose prose-sm prose-invert max-w-none [&_table]:w-full [&_table]:border-collapse [&_table]:my-4 [&_table]:border [&_table]:border-gray-500 [&_th]:border [&_th]:border-gray-500 [&_th]:bg-gray-700 [&_th]:px-3 [&_th]:py-2 [&_th]:text-left [&_th]:font-semibold [&_th]:text-gray-100 [&_td]:border [&_td]:border-gray-600 [&_td]:px-3 [&_td]:py-2 [&_td]:text-gray-200 [&_p]:text-gray-100 [&_p]:leading-relaxed [&_p]:my-2 [&_strong]:text-cyan-300 [&_strong]:font-semibold [&_em]:text-gray-300 [&_h1]:text-white [&_h2]:text-white [&_h3]:text-white [&_h4]:text-white [&_h1]:font-bold [&_h2]:font-bold [&_h3]:font-semibold [&_h4]:font-semibold [&_h1]:text-lg [&_h2]:text-base [&_h3]:text-sm [&_ul]:my-2 [&_ol]:my-2 [&_li]:text-gray-200 [&_li]:my-1 [&_code]:text-cyan-300 [&_code]:bg-gray-900 [&_code]:px-1 [&_code]:rounded [&_code]:text-xs">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{displayContent}</ReactMarkdown>
            </div>
          )}
        </div>

        {/* Copy button - assistant only */}
        {!isUser && (
          <button
            onClick={handleCopy}
            className="absolute -right-8 top-6 rounded p-1 text-gray-600 opacity-0 transition-opacity hover:text-gray-400 group-hover:opacity-100"
            title="Copy"
          >
            {copied ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
          </button>
        )}

        {/* Footer: Confidence + Sources toggle */}
        {!isUser && copilotAnswer && (
          <div className="mt-2 flex flex-wrap items-center gap-3 text-[10px]">
            {/* Confidence */}
            <div className="flex items-center gap-1.5 group/conf relative">
              <span 
                className="uppercase tracking-wide text-gray-500 cursor-help border-b border-dotted border-gray-600"
              >
                Confidence
              </span>
              {/* Hover tooltip with dynamic breakdown */}
              <div className="absolute bottom-full left-0 mb-2 hidden group-hover/conf:block w-64 p-3 rounded-lg bg-gray-900 border border-gray-700 text-[10px] text-gray-300 shadow-xl z-10">
                <div className="font-semibold text-gray-100 mb-2">Score Breakdown:</div>
                
                {/* Current value */}
                <div className="flex justify-between items-center mb-2 pb-2 border-b border-gray-700">
                  <span className="text-gray-400">Final Score</span>
                  <span className={cn(
                    "font-bold text-sm",
                    copilotAnswer.confidence >= 0.8 ? 'text-green-400' :
                    copilotAnswer.confidence >= 0.6 ? 'text-yellow-400' : 'text-red-400'
                  )}>
                    {Math.round(copilotAnswer.confidence * 100)}%
                  </span>
                </div>

                {/* Formula */}
                <div className="space-y-1.5 text-gray-400 mb-2">
                  <div className="flex justify-between">
                    <span>Base (avg source scores)</span>
                    <span className="text-cyan-400 font-mono">~{Math.round(copilotAnswer.confidence * 100 / (copilotAnswer.source_agents?.includes('financial') ? 1.2 : 1))}%</span>
                  </div>
                  {copilotAnswer.source_agents?.includes('financial') && (
                    <div className="flex justify-between">
                      <span>Financial metrics bonus</span>
                      <span className="text-green-400 font-mono">+20%</span>
                    </div>
                  )}
                  {copilotAnswer.alerts && copilotAnswer.alerts.some(a => a.severity === 'high') && (
                    <div className="flex justify-between">
                      <span>High severity penalty</span>
                      <span className="text-red-400 font-mono">−10%</span>
                    </div>
                  )}
                </div>

                {/* Agents used */}
                <div className="pt-2 border-t border-gray-700">
                  <span className="text-gray-500">Sources: </span>
                  <span className="text-gray-300">
                    {citations.length} doc{citations.length !== 1 ? 's' : ''} from {copilotAnswer.source_agents?.join(', ') || 'RAG'}
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-1">
                <div className="h-1.5 w-14 overflow-hidden rounded-full bg-gray-700">
                  <div 
                    className={cn(
                      'h-full rounded-full',
                      copilotAnswer.confidence >= 0.8 ? 'bg-green-500' :
                      copilotAnswer.confidence >= 0.6 ? 'bg-yellow-500' : 'bg-red-500'
                    )}
                    style={{ width: `${copilotAnswer.confidence * 100}%` }}
                  />
                </div>
                <span className={cn(
                  'font-medium',
                  copilotAnswer.confidence >= 0.8 ? 'text-green-400' :
                  copilotAnswer.confidence >= 0.6 ? 'text-yellow-400' : 'text-red-400'
                )}>
                  {Math.round(copilotAnswer.confidence * 100)}%
                </span>
              </div>
            </div>

            {/* Sources toggle */}
            {citations.length > 0 && (
              <button
                onClick={() => setShowSources(!showSources)}
                className="flex items-center gap-1 text-cyan-400 hover:text-cyan-300 transition-colors"
              >
                <FileText className="h-3 w-3" />
                <span>{citations.length} source{citations.length > 1 ? 's' : ''}</span>
                {showSources ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
              </button>
            )}
          </div>
        )}

        {/* Expandable Citations */}
        {!isUser && showSources && citations.length > 0 && (
          <div className="mt-3 rounded-lg bg-gray-800/50 border border-gray-700 p-3 space-y-2">
            <div className="text-[10px] uppercase tracking-wide text-gray-500 mb-2">Referenced Sources</div>
            {citations.map((citation, idx) => (
              <div key={idx} className="flex gap-2 text-xs">
                <span className="flex h-5 w-5 flex-shrink-0 items-center justify-center rounded bg-cyan-600/20 text-cyan-400 text-[10px] font-bold">
                  {idx + 1}
                </span>
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-gray-200 truncate">{citation.source}</div>
                  {citation.page && (
                    <span className="text-gray-500">Page {citation.page}</span>
                  )}
                  {citation.excerpt && citation.excerpt.length > 15 && (
                    <p className="text-gray-400 text-[11px] mt-1 italic line-clamp-2">
                      "{citation.excerpt}"
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  )
}
