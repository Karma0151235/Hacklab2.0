"use client"

import * as React from "react"
import { useRouter } from "next/navigation"
import { Database, FileText, CheckCircle2, Archive, Upload, RefreshCw, HardDrive, ChevronDown, ChevronRight } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { CollectionStats } from "@/lib/types/api"
import { getVectorDBStats, describeCollection, queryEntities } from "@/lib/api/vectordb"
import { cn } from "@/lib/utils"
import { toast } from "sonner"

export default function IngestionPage() {
  const router = useRouter()
  const [isLoading, setIsLoading] = React.useState(true)
  const [vectorStats, setVectorStats] = React.useState<any>(null)
  const [expandedCollections, setExpandedCollections] = React.useState<Set<string>>(new Set())

  const fetchData = React.useCallback(async () => {
    try {
      setIsLoading(true)
      const vdbStats = await getVectorDBStats()
      setVectorStats(vdbStats)
    } catch (error) {
      console.error("Failed to fetch vector database data", error)
      toast.error("Failed to load vector database stats")
    } finally {
      setIsLoading(false)
    }
  }, [])

  React.useEffect(() => {
    fetchData()
  }, [fetchData])

  const toggleCollection = (collectionName: string) => {
    setExpandedCollections(prev => {
      const next = new Set(prev)
      if (next.has(collectionName)) {
        next.delete(collectionName)
      } else {
        next.add(collectionName)
      }
      return next
    })
  }

  return (
    <div className="container mx-auto p-6 space-y-8 max-w-7xl">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-100 flex items-center gap-3">
            <Archive className="h-8 w-8 text-cyan-400" />
            Data Ingestion
          </h1>
          <p className="text-slate-400 mt-2">
            Vector database statistics and ingested document chunks
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
            variant="ghost" 
            size="sm" 
            className="text-slate-400 hover:text-cyan-400"
            onClick={fetchData}
          >
            <RefreshCw className={cn("h-4 w-4 mr-2", isLoading && "animate-spin")} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Vector Database Statistics */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-slate-100 flex items-center gap-2">
            <HardDrive className="h-5 w-5 text-cyan-400" />
            Vector Database
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatsCard 
            title="Total Collections" 
            value={vectorStats?.totalCollections || 0} 
            icon={<Database className="h-4 w-4" />}
            trend={`${vectorStats?.activeCollections || 0} active`}
          />
          <StatsCard 
            title="Total Entities" 
            value={vectorStats?.totalEntities?.toLocaleString() || '0'} 
            icon={<FileText className="h-4 w-4" />}
            trend="Vector chunks"
            className="border-cyan-500/30 bg-cyan-950/10"
          />
          <StatsCard 
            title="Data Size" 
            value={formatBytes(vectorStats?.totalSize || 0)} 
            icon={<HardDrive className="h-4 w-4" />}
            trend="Vector storage"
          />
          <StatsCard 
            title="Active Collections" 
            value={vectorStats?.activeCollections || 0} 
            icon={<CheckCircle2 className="h-4 w-4" />}
            trend="With data"
          />
        </div>

        {/* Collection Breakdown - Expandable */}
        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader>
            <CardTitle className="text-lg">Collections</CardTitle>
            <CardDescription>Browse collection schemas and data</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {!vectorStats?.collectionBreakdown || vectorStats.collectionBreakdown.length === 0 ? (
                <div className="text-center text-slate-500 py-8">
                  No collections found
                </div>
              ) : (
                vectorStats.collectionBreakdown.map((collection: CollectionStats) => (
                  <CollectionCard
                    key={collection.collectionName}
                    collection={collection}
                    isExpanded={expandedCollections.has(collection.collectionName)}
                    onToggle={() => toggleCollection(collection.collectionName)}
                  />
                ))
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <CardTitle className="text-lg">Quick Actions</CardTitle>
          <CardDescription>Manage your data ingestion</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Button 
              variant="outline"
              className="h-auto flex-col items-start p-4 border-slate-700 hover:bg-slate-800"
              onClick={() => router.push('/ingest/upload')}
            >
              <div className="flex items-center gap-2 mb-2">
                <Upload className="h-5 w-5 text-cyan-400" />
                <span className="font-semibold">Upload PDF Files</span>
              </div>
              <p className="text-xs text-slate-400 text-left">
                Upload financial documents for processing and vector storage
              </p>
            </Button>
            
            <Button 
              variant="outline"
              className="h-auto flex-col items-start p-4 border-slate-700 hover:bg-slate-800"
              onClick={() => router.push('/ingest/bursa')}
            >
              <div className="flex items-center gap-2 mb-2">
                <Database className="h-5 w-5 text-cyan-400" />
                <span className="font-semibold">Start Bursa Scraper</span>
              </div>
              <p className="text-xs text-slate-400 text-left">
                Scrape announcements from Bursa Malaysia
              </p>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

function CollectionCard({ 
  collection, 
  isExpanded, 
  onToggle 
}: { 
  collection: CollectionStats
  isExpanded: boolean
  onToggle: () => void
}) {
  const [schema, setSchema] = React.useState<any>(null)
  const [sampleData, setSampleData] = React.useState<any[]>([])
  const [loading, setLoading] = React.useState(false)

  React.useEffect(() => {
    if (isExpanded && !schema) {
      loadCollectionDetails()
    }
  }, [isExpanded])

  const loadCollectionDetails = async () => {
    setLoading(true)
    try {
      const [schemaData, entities] = await Promise.all([
        describeCollection(collection.collectionName),
        queryEntities(collection.collectionName, { limit: 5 })
      ])
      setSchema(schemaData)
      setSampleData(entities)
    } catch (error) {
      console.error("Failed to load collection details", error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="border border-slate-800 rounded-lg bg-slate-900/30 overflow-hidden">
      {/* Collection Header */}
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between p-4 hover:bg-slate-900/50 transition-colors"
      >
        <div className="flex items-center gap-3">
          {isExpanded ? (
            <ChevronDown className="h-4 w-4 text-slate-400" />
          ) : (
            <ChevronRight className="h-4 w-4 text-slate-400" />
          )}
          <div className={cn(
            "h-2 w-2 rounded-full",
            collection.rowCount > 0 ? "bg-cyan-400 shadow-[0_0_8px_rgba(6,182,212,0.8)]" : "bg-slate-600"
          )} />
          <span className="text-sm font-medium text-slate-300 font-mono">
            {collection.collectionName}
          </span>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-xs text-slate-400">
            {collection.rowCount.toLocaleString()} entities
          </span>
          <span className="text-xs text-slate-500 font-mono">
            {formatBytes(collection.dataSize || 0)}
          </span>
        </div>
      </button>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="border-t border-slate-800 p-4">
          {loading ? (
            <div className="text-center text-slate-500 py-4">Loading...</div>
          ) : (
            <Tabs defaultValue="schema" className="w-full">
              <TabsList className="bg-slate-900 border-slate-800">
                <TabsTrigger value="schema" className="data-[state=active]:bg-slate-800">
                  Schema
                </TabsTrigger>
                <TabsTrigger value="data" className="data-[state=active]:bg-slate-800">
                  Sample Data
                </TabsTrigger>
              </TabsList>
              
              <TabsContent value="schema" className="mt-4">
                {schema ? (
                  <div className="space-y-2">
                    {schema.fields?.map((field: any, idx: number) => (
                      <div key={idx} className="flex items-center justify-between p-2 rounded bg-slate-900/50 text-xs">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-cyan-400">{field.name}</span>
                          {field.is_primary && (
                            <span className="px-1.5 py-0.5 bg-amber-500/20 text-amber-400 rounded text-[10px]">
                              PRIMARY
                            </span>
                          )}
                        </div>
                        <span className="text-slate-500">{field.type}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-slate-500 text-sm">No schema available</div>
                )}
              </TabsContent>
              
              <TabsContent value="data" className="mt-4">
                {sampleData.length > 0 ? (
                  <div className="space-y-3">
                    {sampleData.map((entity, idx) => (
                      <div key={idx} className="p-3 rounded bg-slate-900/50 space-y-1">
                        {Object.entries(entity).map(([key, value]) => (
                          <div key={key} className="flex text-xs">
                            <span className="text-slate-500 w-32 flex-shrink-0">{key}:</span>
                            <span className="text-slate-300 font-mono break-all">
                              {typeof value === 'string' && value.length > 100 
                                ? value.substring(0, 100) + '...' 
                                : String(value)}
                            </span>
                          </div>
                        ))}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-slate-500 text-sm">No data available</div>
                )}
              </TabsContent>
            </Tabs>
          )}
        </div>
      )}
    </div>
  )
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`
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
