'use client'

import { useState, useEffect, useMemo, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Slider } from '@/components/ui/slider'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Card } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { PlayIcon, DownloadIcon, FileTextIcon } from 'lucide-react'
import {
  startBursaScraping,
  getBursaScrapingStatus,
  getBursaScrapingResults,
  getBursaScrapingVideoUrl,
  type BursaScrapingStatus,
  type BursaAnnouncementRecord
} from '@/lib/api/ingestion'
import { useBursaScrapeStore } from '@/stores/use-bursa-scrape-store'

export default function BursaScraperPage() {
  // Configuration state
  const [year, setYear] = useState('2024')
  const [companyFilter, setCompanyFilter] = useState('')
  const [maxAnnouncements, setMaxAnnouncements] = useState([10])
  
  const {
    jobId,
    status: jobStatus,
    announcements: results,
    videoAvailable,
    setJobId,
    setStatus,
    setResults,
    clearJob,
  } = useBursaScrapeStore()
  
  // UI state
  const [isStarting, setIsStarting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  // Generate year options (2020-2026)
  const yearOptions = Array.from({ length: 7 }, (_, i) => 2020 + i)
  
  const pollingRef = useRef<NodeJS.Timeout | null>(null)
  const [logFeed, setLogFeed] = useState<string[]>([])

  // Start scraping
  const handleStartScraping = async () => {
    setIsStarting(true)
    setError(null)
    setLogFeed([])
    
    try {
      const response = await startBursaScraping({
        year: parseInt(year),
        max_announcements: maxAnnouncements[0],
        company_filter: companyFilter.trim() || undefined,
        resource_efficient: false,
        use_cloudscraper: false,
        manual_captcha_timeout_seconds: 300
      })
      
      setJobId(response.job_id)
      // Start polling for status
      pollStatus(response.job_id)
    } catch (err: any) {
      setError(err.message || 'Failed to start scraping')
    } finally {
      setIsStarting(false)
    }
  }
  
  // Poll for job status
  const pollStatus = async (currentJobId: string) => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current)
    }

    pollingRef.current = setInterval(async () => {
      try {
        const status = await getBursaScrapingStatus(currentJobId)
        setStatus(status)
        if (status.message) {
          setLogFeed((prev) => [`[${new Date().toLocaleTimeString()}] ${status.message}`, ...prev])
        }
        
        // Stop polling if complete or failed
        if (status.status === 'completed' || status.status === 'failed') {
          if (pollingRef.current) {
            clearInterval(pollingRef.current)
            pollingRef.current = null
          }
          
          // Fetch results if completed
          if (status.status === 'completed') {
            const jobResults = await getBursaScrapingResults(currentJobId)
            setResults(jobResults)
          }
        }
      } catch (err) {
        console.error('Failed to fetch status:', err)
        if (pollingRef.current) {
          clearInterval(pollingRef.current)
          pollingRef.current = null
        }
      }
    }, 2000) // Poll every 2 seconds
    
    // Clear interval after 5 minutes
    setTimeout(() => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current)
        pollingRef.current = null
      }
    }, 5 * 60 * 1000)
  }

  useEffect(() => {
    if (jobId && (!jobStatus || jobStatus.status === 'pending' || jobStatus.status === 'processing')) {
      pollStatus(jobId)
    }

    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current)
        pollingRef.current = null
      }
    }
  }, [jobId])

  const isJobActive = useMemo(() => {
    return jobStatus?.status === 'pending' || jobStatus?.status === 'processing'
  }, [jobStatus?.status])

  const ingestionStats = jobStatus?.ingestion_stats || {}
  
  // Status badge color
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-500'
      case 'processing': return 'bg-blue-500 animate-pulse'
      case 'pending': return 'bg-yellow-500'
      case 'failed': return 'bg-red-500'
      default: return 'bg-gray-500'
    }
  }
  
  return (
    <div className="min-h-screen bg-linear-to-br from-gray-950 via-gray-900 to-gray-950 p-8">
      <div className="mx-auto max-w-6xl space-y-8">
        {/* Page Header */}
        <div className="mb-8">
          <div className="inline-flex items-center gap-2 rounded-full border border-cyan-500/30 bg-cyan-500/10 px-4 py-1 text-xs uppercase tracking-[0.3em] text-cyan-200">
            Bursa Intelligence
          </div>
          <h1 className="mt-4 text-4xl font-semibold text-white">Bursa Malaysia Scraper</h1>
          <p className="text-gray-400">Live ingestion pipeline for Bursa announcements</p>
        </div>
        
        {/* Configuration Card */}
        {!isJobActive && (
          <Card className="border border-gray-800 bg-linear-to-br from-gray-900/80 via-gray-900/40 to-gray-900/20 p-6 shadow-[0_0_40px_rgba(8,145,178,0.08)]">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-white">Configuration</h2>
                <p className="text-sm text-gray-400">Tune scraping parameters before launch.</p>
              </div>
              <Badge className="bg-cyan-500/10 text-cyan-200 border border-cyan-500/20">Manual Mode</Badge>
            </div>

            <div className="mt-6 grid grid-cols-1 gap-6 md:grid-cols-3">
              {/* FY Year */}
              <div className="rounded-xl border border-gray-800 bg-gray-950/60 p-4">
                <Label htmlFor="year" className="text-xs uppercase tracking-[0.3em] text-gray-500">FY Year</Label>
                <Select value={year} onValueChange={setYear}>
                  <SelectTrigger className="mt-3 bg-gray-900/80 border-gray-700 text-white">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-gray-900 border-gray-700">
                    {yearOptions.map((y) => (
                      <SelectItem key={y} value={y.toString()} className="text-white">
                        {y}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Company Filter */}
              <div className="rounded-xl border border-gray-800 bg-gray-950/60 p-4 md:col-span-2">
                <Label htmlFor="company-filter" className="text-xs uppercase tracking-[0.3em] text-gray-500">Company Filter</Label>
                <Input
                  id="company-filter"
                  type="text"
                  placeholder="MAYBANK, CIMB, PCHEM"
                  value={companyFilter}
                  onChange={(e) => setCompanyFilter(e.target.value)}
                  className="mt-3 bg-gray-900/80 border-gray-700 text-white placeholder:text-gray-500"
                />
                <p className="mt-2 text-xs text-gray-500">Leave empty to scrape all companies.</p>
              </div>
            </div>

            {/* Max Announcements Slider */}
            <div className="mt-6 rounded-xl border border-gray-800 bg-gray-950/60 p-4">
              <div className="flex items-center justify-between">
                <Label className="text-xs uppercase tracking-[0.3em] text-gray-500">Max Announcements</Label>
                <span className="text-sm font-semibold text-cyan-200">{maxAnnouncements[0]}</span>
              </div>
              <Slider
                value={maxAnnouncements}
                onValueChange={setMaxAnnouncements}
                min={1}
                max={100}
                step={1}
                className="mt-4 w-full"
              />
              <div className="mt-2 flex justify-between text-xs text-gray-600">
                <span>1</span>
                <span>100</span>
              </div>
            </div>

            {/* Start Button */}
            <div className="mt-6 grid grid-cols-1 gap-3 md:grid-cols-2">
              <Button
                onClick={handleStartScraping}
                disabled={isStarting || isJobActive}
                className="w-full bg-cyan-600 hover:bg-cyan-700 text-white"
              >
                <PlayIcon className="mr-2 h-4 w-4" />
                {isStarting ? 'Starting...' : 'Start Scraping'}
              </Button>
              {jobId && !isJobActive && (
                <Button
                  variant="outline"
                  className="w-full border-gray-700 text-gray-300"
                  onClick={() => clearJob()}
                >
                  Reset Job
                </Button>
              )}
            </div>

            {/* Error Display */}
            {error && (
              <div className="mt-4 rounded border border-red-500/40 bg-red-900/20 p-4 text-red-300">
                {error}
              </div>
            )}
          </Card>
        )}
        
        {/* Progress Display */}
        {jobStatus && (
          <Card className="bg-gray-900/60 border-gray-800 p-6 space-y-6">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-semibold text-white">Scraping Progress</h3>
              <Badge className={`${getStatusColor(jobStatus.status)} text-white`}>
                {jobStatus.status.toUpperCase()}
              </Badge>
            </div>
            
            {/* Progress Bar */}
            <div className="space-y-3">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-400">Progress</span>
                <span className="text-gray-300">{jobStatus.progress}% • {jobStatus.phase}</span>
              </div>
              <Progress value={jobStatus.progress} className="h-2 bg-gray-900" />
              {jobStatus.message && (
                <p className="text-xs text-cyan-300">{jobStatus.message}</p>
              )}
            </div>

            {/* Active Context */}
            {(jobStatus.current_company || jobStatus.current_title || jobStatus.current_url) && (
              <div className="rounded-xl border border-gray-800 bg-gray-950/60 p-4 text-sm text-gray-300">
                <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                  <div>
                    <p className="text-xs uppercase tracking-[0.2em] text-gray-500">Target</p>
                    <p className="text-sm text-gray-200">
                      {jobStatus.target_companies?.length
                        ? jobStatus.target_companies.join(', ')
                        : 'All companies'}
                      {jobStatus.current_year ? ` • FY${jobStatus.current_year}` : ''}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-[0.2em] text-gray-500">Category</p>
                    <p className="text-sm text-gray-200">
                      {jobStatus.current_category || 'All categories'}
                    </p>
                  </div>
                </div>
                {jobStatus.current_title && (
                  <div className="mt-3">
                    <p className="text-xs uppercase tracking-[0.2em] text-gray-500">Now Scraping</p>
                    <p className="text-sm text-cyan-200">{jobStatus.current_title}</p>
                  </div>
                )}
                {jobStatus.current_url && (
                  <a
                    href={jobStatus.current_url}
                    target="_blank"
                    rel="noreferrer"
                    className="mt-2 block truncate text-xs text-cyan-400 hover:text-cyan-300"
                  >
                    {jobStatus.current_url}
                  </a>
                )}
              </div>
            )}
            
            {/* Stats */}
            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              <div className="rounded-xl border border-cyan-500/20 bg-linear-to-br from-cyan-950/40 via-gray-900/70 to-gray-900 p-4">
                <p className="text-xs uppercase tracking-[0.2em] text-cyan-300">Scraped</p>
                <p className="mt-3 text-3xl font-semibold text-white">
                  {jobStatus.scraped_announcements}
                </p>
                <p className="text-xs text-gray-400">of {jobStatus.total_announcements} announcements</p>
              </div>
              <div className="rounded-xl border border-purple-500/20 bg-linear-to-br from-purple-950/30 via-gray-900/70 to-gray-900 p-4">
                <p className="text-xs uppercase tracking-[0.2em] text-purple-300">Chunks</p>
                <p className="mt-3 text-3xl font-semibold text-white">
                  {ingestionStats.chunks_created ?? 0}
                </p>
                <p className="text-xs text-gray-400">processed for embeddings</p>
              </div>
              <div className="rounded-xl border border-rose-500/20 bg-linear-to-br from-rose-950/30 via-gray-900/70 to-gray-900 p-4">
                <p className="text-xs uppercase tracking-[0.2em] text-rose-300">Errors</p>
                <p className="mt-3 text-3xl font-semibold text-white">
                  {jobStatus.errors.length}
                </p>
                <p className="text-xs text-gray-400">runtime warnings</p>
              </div>
            </div>

            {/* Ingestion stats */}
            {jobStatus.ingestion_status && (
              <div className="rounded-xl border border-gray-700/60 bg-gray-900/60 p-4 text-sm text-gray-300">
                <div className="flex items-center justify-between">
                  <span className="font-medium text-gray-200">Ingestion</span>
                  <span className="text-xs text-gray-400">{jobStatus.ingestion_status}</span>
                </div>
                <div className="mt-3 grid grid-cols-2 gap-3 text-xs text-gray-400 md:grid-cols-4">
                  <div>
                    <p className="text-gray-500">Docs</p>
                    <p className="text-gray-200">{ingestionStats.documents_processed ?? 0}</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Tables</p>
                    <p className="text-gray-200">{ingestionStats.tables_inserted ?? 0}</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Embeddings</p>
                    <p className="text-gray-200">{ingestionStats.embeddings_generated ?? 0}</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Records</p>
                    <p className="text-gray-200">{ingestionStats.records_inserted ?? 0}</p>
                  </div>
                </div>
              </div>
            )}
            
            {/* Errors */}
            {jobStatus.errors.length > 0 && (
              <div className="space-y-2">
                <p className="text-sm font-medium text-red-400">Errors:</p>
                <div className="bg-red-900/20 border border-red-500 rounded p-3 space-y-1">
                  {jobStatus.errors.map((err, idx) => (
                    <p key={idx} className="text-xs text-red-300">{err}</p>
                  ))}
                </div>
              </div>
            )}
          </Card>
        )}

        {jobStatus && (
          <Card className="border border-gray-800 bg-gray-950/70 p-6">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-white">Live Logs</h3>
              <span className="text-xs uppercase tracking-[0.3em] text-gray-500">Live Feed</span>
            </div>
            <div className="h-56 overflow-hidden rounded-xl border border-gray-800 bg-black/60 p-4 font-mono text-xs text-emerald-300">
              <div className="h-full overflow-y-auto pr-2">
                {logFeed.length === 0 && (
                  <p className="text-gray-500">No logs yet. Waiting for updates...</p>
                )}
                {logFeed.map((line, idx) => (
                  <p key={`${line}-${idx}`} className="whitespace-pre-wrap">
                    {line}
                  </p>
                ))}
              </div>
            </div>
          </Card>
        )}
        
        {/* Results Table */}
        {results.length > 0 && (
          <Card className="bg-gray-800/50 border-gray-700 p-6 space-y-4">
            <h3 className="text-lg font-semibold text-white">
              Results ({results.length} announcements)
            </h3>
            
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-700">
                    <th className="text-left p-3 text-gray-400">Company</th>
                    <th className="text-left p-3 text-gray-400">Date</th>
                    <th className="text-left p-3 text-gray-400">Title</th>
                    <th className="text-right p-3 text-gray-400">Tables</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((announcement, idx) => (
                    <tr key={idx} className="border-b border-gray-700/50 hover:bg-gray-700/20">
                      <td className="p-3 text-cyan-400 font-mono">
                        {announcement.company_code || 'N/A'}
                      </td>
                      <td className="p-3 text-gray-300">
                        {announcement.announcement_date}
                      </td>
                      <td className="p-3 text-gray-200">
                        {announcement.title.substring(0, 60)}...
                      </td>
                      <td className="p-3 text-right text-gray-400">
                        {announcement.tables_count}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        )}
        
        {/* Video Player */}
        {videoAvailable && jobId && (
          <Card className="bg-gray-800/50 border-gray-700 p-6 space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-semibold text-white">Recording</h3>
              <Button
                variant="outline"
                size="sm"
                asChild
                className="border-gray-600 text-cyan-400"
              >
                <a href={getBursaScrapingVideoUrl(jobId)} download>
                  <DownloadIcon className="mr-2 h-4 w-4" />
                  Download Video
                </a>
              </Button>
            </div>
            
            <div className="relative bg-black rounded overflow-hidden aspect-video">
              <video
                controls
                className="w-full h-full"
                src={getBursaScrapingVideoUrl(jobId)}
              >
                Your browser does not support video playback.
              </video>
            </div>
          </Card>
        )}
      </div>
    </div>
  )
}
