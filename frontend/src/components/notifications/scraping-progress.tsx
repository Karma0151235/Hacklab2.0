"use client"

import * as React from "react"
import { Monitor, FileText, CheckCircle2, Loader2, PlayCircle, AlertCircle, Terminal } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

export interface LogEntry {
  timestamp: string
  message: string
  type: 'info' | 'success' | 'warning' | 'error'
}

interface ScrapingProgressProps {
  jobId: string
  status: 'queued' | 'running' | 'completed' | 'failed'
  phase: string
  progress: number
  documentCount: number
  totalDocuments: number
  logs: LogEntry[]
  videoUrl?: string // For mock video preview
  onCancel?: () => void
}

export function ScrapingProgress({
  jobId,
  status,
  phase,
  progress,
  documentCount,
  totalDocuments,
  logs,
  videoUrl,
  onCancel
}: ScrapingProgressProps) {
  const scrollRef = React.useRef<HTMLDivElement>(null)

  // Auto-scroll logs
  React.useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [logs])

  return (
    <Card className="w-full border-cyan-500/20 bg-slate-950/50 backdrop-blur-sm overflow-hidden">
      <CardHeader className="pb-4 border-b border-slate-800/60">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <CardTitle className="flex items-center gap-2 text-lg font-medium text-slate-100">
              <Monitor className="h-5 w-5 text-cyan-400" />
              Bursa Malaysia Scraper
              <Badge variant="outline" className={cn(
                "ml-2 font-mono text-xs uppercase tracking-wider",
                status === 'running' && "border-cyan-500/50 text-cyan-400 bg-cyan-950/30 animate-pulse",
                status === 'completed' && "border-emerald-500/50 text-emerald-400 bg-emerald-950/30",
                status === 'failed' && "border-red-500/50 text-red-400 bg-red-950/30",
                status === 'queued' && "border-slate-500/50 text-slate-400 bg-slate-950/30"
              )}>
                {status}
              </Badge>
            </CardTitle>
            <CardDescription className="font-mono text-xs text-slate-400">
              Job ID: {jobId}
            </CardDescription>
          </div>
          {status === 'running' && (
             <button 
               onClick={onCancel}
               className="text-xs text-red-400 hover:text-red-300 transition-colors font-mono hover:underline"
             >
               CANCEL JOB
             </button>
          )}
        </div>
      </CardHeader>
      
      <CardContent className="pt-6 space-y-6">
        {/* Progress Section */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-slate-300 font-medium">{phase}</span>
            <span className="font-mono text-cyan-400">{progress}%</span>
          </div>
          <Progress value={progress} className="h-2 bg-slate-800" indicatorClassName="bg-cyan-500 shadow-[0_0_10px_rgba(6,182,212,0.5)]" />
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 gap-4">
          <div className="p-3 rounded-lg bg-slate-900/50 border border-slate-800/60 flex items-center gap-3">
             <div className="h-10 w-10 rounded-full bg-slate-800 flex items-center justify-center text-slate-400">
               <FileText className="h-5 w-5" />
             </div>
             <div>
               <p className="text-xs text-slate-500 uppercase tracking-wide font-semibold">Documents</p>
               <p className="font-mono text-xl text-slate-100">
                 {documentCount} <span className="text-slate-500 text-sm">/ {totalDocuments > 0 ? totalDocuments : '?'}</span>
               </p>
             </div>
          </div>
          
          <div className="p-3 rounded-lg bg-slate-900/50 border border-slate-800/60 flex items-center gap-3">
             <div className="h-10 w-10 rounded-full bg-slate-800 flex items-center justify-center text-slate-400">
               {status === 'completed' ? <CheckCircle2 className="h-5 w-5 text-emerald-400" /> : <Loader2 className="h-5 w-5 animate-spin text-cyan-400" />}
             </div>
             <div>
               <p className="text-xs text-slate-500 uppercase tracking-wide font-semibold">Time Elapsed</p>
               <p className="font-mono text-xl text-slate-100">00:02:14</p>
             </div>
          </div>
        </div>

        {/* Live Logs & Video Preview */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Logs */}
          <div className="md:col-span-2 space-y-2">
            <div className="flex items-center gap-2 text-xs text-slate-400 uppercase tracking-wider font-semibold">
              <Terminal className="h-3 w-3" /> Live Logs
            </div>
            <div 
              className="h-48 rounded-md bg-slate-950 border border-slate-800 p-4 overflow-y-auto font-mono text-xs"
              ref={scrollRef}
            >
              <div className="space-y-1.5">
                <AnimatePresence initial={false}>
                  {logs.map((log, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      className={cn(
                        "flex gap-3",
                        log.type === 'error' && "text-red-400",
                        log.type === 'warning' && "text-amber-400",
                        log.type === 'success' && "text-emerald-400",
                        log.type === 'info' && "text-slate-300"
                      )}
                    >
                      <span className="text-slate-600 shrink-0">[{log.timestamp}]</span>
                      <span>{log.message}</span>
                    </motion.div>
                  ))}
                </AnimatePresence>
                {status === 'running' && (
                   <motion.div 
                     initial={{ opacity: 0 }} 
                     animate={{ opacity: 1 }} 
                     transition={{ repeat: Infinity, duration: 0.8 }}
                     className="text-cyan-500/50"
                   >
                     _
                   </motion.div>
                )}
              </div>
            </div>
          </div>

          {/* Video Preview */}
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-xs text-slate-400 uppercase tracking-wider font-semibold">
              <PlayCircle className="h-3 w-3" /> Browser View
            </div>
            <div className="aspect-video w-full rounded-md bg-slate-900 border border-slate-800 overflow-hidden relative group">
              {status === 'running' || status === 'completed' ? (
                <div className="w-full h-full bg-slate-800 flex items-center justify-center relative">
                   {/* Mock Browser Interface */}
                   <div className="absolute inset-0 p-2 opacity-50">
                     <div className="w-full h-4 bg-slate-700 rounded-sm mb-2 flex items-center px-2 gap-1">
                       <div className="h-2 w-2 rounded-full bg-red-500"></div>
                       <div className="h-2 w-2 rounded-full bg-amber-500"></div>
                       <div className="h-2 w-2 rounded-full bg-emerald-500"></div>
                     </div>
                     <div className="space-y-2">
                       <div className="h-2 w-3/4 bg-slate-600 rounded"></div>
                       <div className="h-2 w-1/2 bg-slate-600 rounded"></div>
                       <div className="h-20 w-full bg-slate-700 rounded mt-4"></div>
                     </div>
                   </div>
                   
                   <div className="z-10 bg-slate-950/80 backdrop-blur px-3 py-1.5 rounded-full border border-slate-700 flex items-center gap-2">
                     <div className="h-2 w-2 rounded-full bg-red-500 animate-pulse"></div>
                     <span className="text-[10px] font-mono font-medium text-slate-300">REC</span>
                   </div>
                </div>
              ) : (
                <div className="w-full h-full flex flex-col items-center justify-center text-slate-600 gap-2">
                   <Monitor className="h-8 w-8 opacity-50" />
                   <span className="text-xs">Waiting to start...</span>
                </div>
              )}
            </div>
            <p className="text-[10px] text-slate-500">
              * Debugging view recorded from headless browser session
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
