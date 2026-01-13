"use client"

import * as React from "react"
import { useRouter } from "next/navigation"
import { Play, Database, Calendar, Filter, FileText, ArrowLeft, CheckCircle2 } from "lucide-react"
import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import * as z from "zod"
import { format } from "date-fns"

import { Button } from "@/components/ui/button"
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { Slider } from "@/components/ui/slider"
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { ScrapingProgress, LogEntry } from "@/components/notifications/scraping-progress"
import { startBursaScrapingJob, getJobPhase, getScrapingLogs } from "@/lib/api/ingestion"
import { IngestionJob } from "@/lib/types/api"
import { toast } from "sonner"

const formSchema = z.object({
  year: z.string({
    message: "Please select a year to scrape.",
  }),
  maxAnnouncements: z.number().min(10).max(5000),
  companies: z.string().optional(),
})

export default function BursaScraperPage() {
  const router = useRouter()
  const [job, setJob] = React.useState<IngestionJob | null>(null)
  const [logs, setLogs] = React.useState<LogEntry[]>([])
  const [isFinishing, setIsFinishing] = React.useState(false)

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      year: "2024",
      maxAnnouncements: 100,
      companies: "",
    },
  })

  // Poll for updates when job is running
  React.useEffect(() => {
    if (!job || job.status !== 'running') return

    const interval = setInterval(() => {
      setJob(prev => {
        if (!prev) return null
        
        // Simulate progress
        const newProgress = Math.min(prev.progress + 2, 100)
        
        // If completed
        if (newProgress >= 100 && !isFinishing) {
           setIsFinishing(true)
           setTimeout(() => {
             setJob(j => j ? { ...j, status: 'completed', progress: 100 } : null)
             toast.success("Scraping job completed successfully")
           }, 1000)
        }
        
        return { 
          ...prev, 
          progress: newProgress,
          processed_documents: Math.floor((newProgress / 100) * prev.total_documents)
        }
      })

      // Add mock logs
      if (Math.random() > 0.6) {
        setLogs(prev => [...prev, {
          timestamp: format(new Date(), 'HH:mm:ss'),
          message: `Extracted table data from announcement ${Math.floor(Math.random() * 1000)}...`,
          type: (Math.random() > 0.9 ? 'warning' : 'info') as LogEntry['type']
        }].slice(-20)) // Keep last 20
      }

    }, 1000)

    return () => clearInterval(interval)
  }, [job, isFinishing])

  async function onSubmit(values: z.infer<typeof formSchema>) {
    try {
      const newJob = await startBursaScrapingJob({
        year: parseInt(values.year),
        maxAnnouncements: values.maxAnnouncements,
        companyFilter: values.companies ? values.companies.split(',').map(s => s.trim()) : undefined
      })
      
      setJob(newJob)
      setLogs([{
        timestamp: format(new Date(), 'HH:mm:ss'),
        message: "Initializing Bursa Malaysia scraper...",
        type: 'info'
      }])
      toast.success("Scraping job started")
    } catch (error) {
      toast.error("Failed to start scraping job")
    }
  }

  const handleReset = () => {
    setJob(null)
    setLogs([])
    setIsFinishing(false)
    form.reset()
  }

  return (
    <div className="container mx-auto p-6 space-y-8 max-w-5xl animate-in fade-in duration-500">
      
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button 
          variant="ghost" 
          size="icon" 
          onClick={() => router.back()}
          className="text-slate-400 hover:text-slate-100 ring-1 ring-slate-800"
        >
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
           <h1 className="text-3xl font-bold tracking-tight text-slate-100 flex items-center gap-3">
            <Database className="h-8 w-8 text-cyan-400" />
            Bursa Malaysia Scraper
          </h1>
          <p className="text-slate-400 mt-1">
            Configure and run automated scraping jobs for Bursa Malaysia announcements.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Configuration Form */}
        <div className="lg:col-span-1">
          <Card className="border-slate-800 bg-slate-950/50 sticky top-6">
            <CardHeader>
              <CardTitle>Configuration</CardTitle>
              <CardDescription>Set parameters for the scraping job.</CardDescription>
            </CardHeader>
            <CardContent>
              <Form {...form}>
                <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
                  
                  <FormField
                    control={form.control}
                    name="year"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>FY Year</FormLabel>
                        <Select onValueChange={field.onChange} defaultValue={field.value} disabled={!!job}>
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue placeholder="Select year" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            <SelectItem value="2025">2025</SelectItem>
                            <SelectItem value="2024">2024</SelectItem>
                            <SelectItem value="2023">2023</SelectItem>
                            <SelectItem value="2022">2022</SelectItem>
                          </SelectContent>
                        </Select>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="companies"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Company Filter (Optional)</FormLabel>
                        <FormControl>
                          <Input placeholder="e.g. MAYBANK, CIMB, PCHEM" {...field} disabled={!!job} />
                        </FormControl>
                        <FormDescription>
                          Leave empty to scrape all companies. Comma separated.
                        </FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="maxAnnouncements"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Max Announcements: {field.value}</FormLabel>
                        <FormControl>
                          <Slider
                            min={10}
                            max={1000}
                            step={10}
                            defaultValue={[field.value]}
                            onValueChange={(vals) => field.onChange(vals[0])}
                            disabled={!!job}
                            className="py-4"
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <Button 
                    type="submit" 
                    className="w-full bg-cyan-500 hover:bg-cyan-600 text-slate-950 font-bold"
                    disabled={!!job}
                  >
                    {!job ? (
                      <>
                        <Play className="mr-2 h-4 w-4" /> Start Scraping
                      </>
                    ) : (
                      <>
                        <CheckCircle2 className="mr-2 h-4 w-4" /> Job Created
                      </>
                    )}
                  </Button>
                </form>
              </Form>
            </CardContent>
          </Card>
        </div>

        {/* Progress / Output */}
        <div className="lg:col-span-2">
          {!job ? (
            <div className="h-full min-h-[400px] flex flex-col items-center justify-center border-2 border-dashed border-slate-800 rounded-lg bg-slate-950/20 text-slate-500">
               <Database className="h-16 w-16 mb-4 opacity-20" />
               <h3 className="text-lg font-medium">Ready to scrape</h3>
               <p className="text-sm">Configure the job on the left and click start.</p>
            </div>
          ) : (
            <div className="space-y-6">
              <ScrapingProgress 
                jobId={job.job_id}
                status={job.status}
                phase={getJobPhase(job.progress)}
                progress={job.progress}
                documentCount={job.processed_documents}
                totalDocuments={job.total_documents}
                logs={logs}
                onCancel={() => setJob(prev => prev ? {...prev, status: 'failed'} : null)}
              />

              {job.status === 'completed' && (
                <Card className="bg-emerald-950/10 border-emerald-500/20">
                  <CardHeader>
                    <CardTitle className="text-emerald-400 flex items-center gap-2">
                      <CheckCircle2 className="h-5 w-5" /> Job Completed
                    </CardTitle>
                    <CardDescription>
                      Successfully processed {job.processed_documents} documents.
                    </CardDescription>
                  </CardHeader>
                  <CardFooter>
                    <Button variant="outline" onClick={handleReset} className="w-full">
                      Run Another Job
                    </Button>
                  </CardFooter>
                </Card>
              )}
            </div>
          )}
        </div>

      </div>
    </div>
  )
}
