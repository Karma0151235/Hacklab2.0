"use client"

import * as React from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { Database, Play, BarChart3, FileText, AlertTriangle, CheckCircle2, MoreVertical, Archive, Upload, Loader2, RefreshCw } from "lucide-react"
import { format } from "date-fns"


import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { DataTable } from "@/components/data-display/data-table"
import { ScrapingProgress, LogEntry } from "@/components/notifications/scraping-progress"
import { getIngestionJobs, getIngestionStats, getJobPhase, getScrapingLogs, cancelIngestionJob } from "@/lib/api/ingestion"
import { IngestionJob } from "@/lib/types/api"
import { cn } from "@/lib/utils"
import { toast } from "sonner"

export default function IngestionPage() {
  const router = useRouter()
  const [jobs, setJobs] = React.useState<IngestionJob[]>([])
  const [stats, setStats] = React.useState<any>(null)
  const [isLoading, setIsLoading] = React.useState(true)
  const [runningJob, setRunningJob] = React.useState<IngestionJob | null>(null)
  const [activeLogs, setActiveLogs] = React.useState<LogEntry[]>([])

  const fetchData = React.useCallback(async () => {
    try {
      setIsLoading(true)
      const [fetchedJobs, fetchedStats] = await Promise.all([
        getIngestionJobs(),
        getIngestionStats()
      ])
      
      setJobs(fetchedJobs)
      setStats(fetchedStats)
      
      // Check for running job
      const active = fetchedJobs.find(j => j.status === 'running')
      if (active) {
        setRunningJob(active)
        // Fetch logs for the running job
        const logs = await getScrapingLogs(active.job_id)
        setActiveLogs(logs.map(l => ({
            timestamp: format(new Date(l.timestamp), 'HH:mm:ss'),
            message: l.message,
            type: l.level
        })))
      } else {
        setRunningJob(null)
      }
    } catch (error) {
      console.error("Failed to fetch ingestion data", error)
      toast.error("Failed to load ingestion data")
    } finally {
      setIsLoading(false)
    }
  }, [])

  React.useEffect(() => {
    fetchData()
  }, [fetchData])

  // Mock live update
  React.useEffect(() => {
    if (!runningJob) return

    const interval = setInterval(() => {
      setRunningJob(prev => {
        if (!prev) return null
        // Increment progress slightly for simulation
        const newProgress = Math.min(prev.progress + 1, 99)
        return { ...prev, progress: newProgress }
      })
      
      // Add a random log occasionally
      if (Math.random() > 0.7) {
        setActiveLogs(prev => [...prev, {
          timestamp: format(new Date(), 'HH:mm:ss'),
          message: `Processing batch ${Math.floor(Math.random() * 100)}...`,
          type: 'info'
        }])
      }
    }, 2000)

    return () => clearInterval(interval)
  }, [runningJob])

  const handleCancelJob = async () => {
    if (!runningJob) return
    try {
      await cancelIngestionJob(runningJob.job_id)
      toast.success("Job canceled successfully")
      fetchData()
    } catch (error) {
      toast.error("Failed to cancel job")
    }
  }

  const columns = [
    {
      key: "job_id",
      label: "Job ID",
      render: (job: IngestionJob) => <span className="font-mono text-xs">{job.job_id}</span>,
    },
    {
      key: "type",
      label: "Type",
      render: (job: IngestionJob) => {
        const type = job.type
        return (
          <div className="flex items-center gap-2">
            {type === 'bursa' && <Database className="h-3 w-3 text-cyan-400" />}
            {type === 'manual' && <Upload className="h-3 w-3 text-emerald-400" />}
            {type === 'news' && <FileText className="h-3 w-3 text-amber-400" />}
            <span className="capitalize">{type}</span>
          </div>
        )
      },
    },
    {
      key: "status",
      label: "Status",
      render: (job: IngestionJob) => {
        const status = job.status
        return (
          <Badge variant="outline" className={cn(
            "text-xs capitalize",
            status === 'running' && "border-cyan-500/50 text-cyan-400 bg-cyan-950/30",
            status === 'completed' && "border-emerald-500/50 text-emerald-400 bg-emerald-950/30",
            status === 'failed' && "border-red-500/50 text-red-400 bg-red-950/30",
            status === 'queued' && "border-slate-500/50 text-slate-400 bg-slate-950/30"
          )}>
            {status}
          </Badge>
        )
      },
    },
    {
      key: "progress",
      label: "Progress",
      render: (job: IngestionJob) => {
        const progress = job.progress
        return (
          <div className="w-[100px]">
             <div className="flex justify-between text-[10px] mb-1 text-slate-400">
               <span>{progress}%</span>
             </div>
             <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
               <div 
                 className="h-full bg-cyan-500 rounded-full" 
                 style={{ width: `${progress}%` }}
               />
             </div>
          </div>
        )
      }
    },
    {
      key: "started_at",
      label: "Started At",
      render: (job: IngestionJob) => (
        <span className="text-slate-400 text-xs">
          {format(new Date(job.started_at), "MMM d, yyyy HH:mm")}
        </span>
      ),
    },
    {
      key: "total_documents",
      label: "Docs",
      render: (job: IngestionJob) => (
        <span className="font-mono text-xs">{job.total_documents}</span>
      ),
    },
  ]

  return (
    <div className="container mx-auto p-6 space-y-8 max-w-7xl animate-in fade-in duration-500">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-100 flex items-center gap-3">
            <Archive className="h-8 w-8 text-cyan-400" />
            Data Ingestion
          </h1>
          <p className="text-slate-400 mt-2">
            Manage data scraping jobs, manual uploads, and monitor ingestion progress.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button 
            variant="outline" 
            className="border-slate-700 hover:bg-slate-800 text-slate-300 gap-2"
            onClick={() => router.push('/ingest/upload')}
          >
            <Upload className="h-4 w-4" />
            Upload Files
          </Button>
          <Button 
            className="bg-cyan-500 hover:bg-cyan-600 text-slate-950 font-bold gap-2 shadow-[0_0_15px_rgba(6,182,212,0.5)]"
            onClick={() => router.push('/ingest/bursa')}
          >
            <Play className="h-4 w-4" />
            Start Scraper
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard 
          title="Total Jobs" 
          value={stats?.total || 0} 
          icon={<Database className="h-4 w-4" />}
          trend="All time"
        />
        <StatsCard 
          title="Running Jobs" 
          value={stats?.running || 0} 
          icon={<Loader2 className="h-4 w-4" />}
          className={stats?.running > 0 ? "border-cyan-500/50 bg-cyan-950/10" : ""}
          trend="Currently active"
        />
        <StatsCard 
          title="Documents Processed" 
          value={stats?.totalDocuments || 0} 
          icon={<FileText className="h-4 w-4" />}
          trend="Pages & files"
        />
        <StatsCard 
          title="Success Rate" 
          value={`${stats?.successRate || 0}%`} 
          icon={<CheckCircle2 className="h-4 w-4" />}
          trend="Completion rate"
        />
      </div>

      {/* Active Job Progress */}
      {runningJob && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-slate-100 flex items-center gap-2">
              <Loader2 className="h-5 w-5 animate-spin text-cyan-400" />
              Active Job
            </h2>
          </div>
          <ScrapingProgress 
            jobId={runningJob.job_id}
            status={runningJob.status}
            phase={getJobPhase(runningJob.progress)}
            progress={runningJob.progress}
            documentCount={runningJob.processed_documents}
            totalDocuments={runningJob.total_documents}
            logs={activeLogs}
            onCancel={handleCancelJob}
          />
        </div>
      )}

      {/* Job History Table */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-slate-100">Job History</h2>
          <Button 
            variant="ghost" 
            size="sm" 
            className="text-slate-400 hover:text-cyan-400"
            onClick={fetchData}
          >
            <RefreshCw className={cn("h-4 w-4 mr-2", isLoading && "animate-spin")} />
            Refresh
          </Button>
        </div>
        
        <Card className="border-slate-800 bg-slate-950/50">
          <CardContent className="p-0">
             <DataTable 
               columns={columns} 
               data={jobs} 
               keyExtractor={(job) => job.job_id}
             />
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

function StatsCard({ 
  title, 
  value, 
  icon, 
  className,
  trend 
}: { 
  title: string, 
  value: string | number, 
  icon: React.ReactNode, 
  className?: string,
  trend?: string
}) {
  return (
    <Card className={cn("border-slate-800 bg-slate-950/50 backdrop-blur hover:border-slate-700 transition-all duration-300", className)}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-slate-400">
          {title}
        </CardTitle>
        <div className="text-slate-400">
          {icon}
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold text-slate-100 font-mono">{value}</div>
        {trend && (
          <p className="text-xs text-slate-500 mt-1">
            {trend}
          </p>
        )}
      </CardContent>
    </Card>
  )
}
