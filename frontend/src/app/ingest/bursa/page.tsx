'use client'

import { useState, useEffect } from 'react'
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

export default function BursaScraperPage() {
  // Configuration state
  const [year, setYear] = useState('2024')
  const [companyFilter, setCompanyFilter] = useState('')
  const [maxAnnouncements, setMaxAnnouncements] = useState([10])
  
  // Job state
  const [jobId, setJobId] = useState<string | null>(null)
  const [jobStatus, setJobStatus] = useState<BursaScrapingStatus | null>(null)
  const [results, setResults] = useState<BursaAnnouncementRecord[]>([])
  const [videoAvailable, setVideoAvailable] = useState(false)
  
  // UI state
  const [isStarting, setIsStarting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  // Generate year options (2020-2026)
  const yearOptions = Array.from({ length: 7 }, (_, i) => 2020 + i)
  
  // Start scraping
  const handleStartScraping = async () => {
    setIsStarting(true)
    setError(null)
    
    try {
      const response = await startBursaScraping({
        year: parseInt(year),
        max_announcements: maxAnnouncements[0],
        company_filter: companyFilter.trim() || undefined
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
    const interval = setInterval(async () => {
      try {
        const status = await getBursaScrapingStatus(currentJobId)
        setJobStatus(status)
        
        // Stop polling if complete or failed
        if (status.status === 'completed' || status.status === 'failed') {
          clearInterval(interval)
          
          // Fetch results if completed
          if (status.status === 'completed') {
            const jobResults = await getBursaScrapingResults(currentJobId)
            setResults(jobResults.announcements)
            setVideoAvailable(jobResults.video_available)
          }
        }
      } catch (err) {
        console.error('Failed to fetch status:', err)
        clearInterval(interval)
      }
    }, 2000) // Poll every 2 seconds
    
    // Clear interval after 5 minutes
    setTimeout(() => clearInterval(interval), 5 * 60 * 1000)
  }
  
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
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-8">
      <div className="mx-auto max-w-6xl space-y-8">
        {/* Page Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-cyan-400 mb-2">Bursa Malaysia Scraper</h1>
          <p className="text-gray-400">Extract financial announcements from Bursa Malaysia</p>
        </div>
        
        {/* Configuration Card */}
        <Card className="bg-gray-800/50 border-gray-700 p-6 space-y-6">
          <div>
            <h2 className="text-xl font-semibold text-white mb-2">Configuration</h2>
            <p className="text-sm text-gray-400">Set parameters for the scraping job.</p>
          </div>
          
          {/* FY Year */}
          <div className="space-y-2">
            <Label htmlFor="year" className="text-white">FY Year</Label>
            <Select value={year} onValueChange={setYear}>
              <SelectTrigger className="bg-gray-900 border-gray-600 text-white">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-gray-900 border-gray-600">
                {yearOptions.map((y) => (
                  <SelectItem key={y} value={y.toString()} className="text-white">
                    {y}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          
          {/* Company Filter */}
          <div className="space-y-2">
            <Label htmlFor="company-filter" className="text-white">Company Filter (Optional)</Label>
            <Input
              id="company-filter"
              type="text"
              placeholder="e.g. MAYBANK, CIMB, PCHEM"
              value={companyFilter}
              onChange={(e) => setCompanyFilter(e.target.value)}
              className="bg-gray-900 border-gray-600 text-white placeholder:text-gray-500"
            />
            <p className="text-sm text-gray-400">
              Leave empty to scrape all companies. Comma separated.
            </p>
          </div>
          
          {/* Max Announcements Slider */}
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <Label className="text-white">Max Announcements: {maxAnnouncements[0]}</Label>
            </div>
            <Slider
              value={maxAnnouncements}
              onValueChange={setMaxAnnouncements}
              min={1}
              max={100}
              step={1}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-500">
              <span>1</span>
              <span>100</span>
            </div>
          </div>
          
          {/* Start Button */}
          <Button
            onClick={handleStartScraping}
            disabled={isStarting || !!jobId}
            className="w-full bg-cyan-600 hover:bg-cyan-700 text-white"
          >
            <PlayIcon className="mr-2 h-4 w-4" />
            {isStarting ? 'Starting...' : 'Start Scraping'}
          </Button>
          
          {/* Error Display */}
          {error && (
            <div className="p-4 bg-red-900/20 border border-red-500 rounded text-red-400">
              {error}
            </div>
          )}
        </Card>
        
        {/* Progress Display */}
        {jobStatus && (
          <Card className="bg-gray-800/50 border-gray-700 p-6 space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-semibold text-white">Scraping Progress</h3>
              <Badge className={`${getStatusColor(jobStatus.status)} text-white`}>
                {jobStatus.status.toUpperCase()}
              </Badge>
            </div>
            
            {/* Progress Bar */}
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Progress: {jobStatus.progress}%</span>
                <span className="text-gray-400">{jobStatus.phase}</span>
              </div>
              <Progress value={jobStatus.progress} className="h-2" />
            </div>
            
            {/* Stats */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-900/50 p-3 rounded">
                <p className="text-xs text-gray-400">Scraped</p>
                <p className="text-2xl font-bold text-cyan-400">
                  {jobStatus.scraped_announcements}/{jobStatus.total_announcements}
                </p>
              </div>
              <div className="bg-gray-900/50 p-3 rounded">
                <p className="text-xs text-gray-400">Errors</p>
                <p className="text-2xl font-bold text-red-400">
                  {jobStatus.errors.length}
                </p>
              </div>
            </div>
            
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
