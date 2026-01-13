'use client'

import { useState, useEffect } from 'react'
import { executeNaturalLanguageQuery, getQueryHistory, exportQueryResultsToCSV, SQLQueryResult } from '@/lib/api/sql'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Play, Download, History, Clock, FileCode, CheckCircle2, Loader2 } from 'lucide-react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { toast } from 'sonner' 

export default function SQLPage() {
  const [query, setQuery] = useState('')
  const [isExecuting, setIsExecuting] = useState(false)
  const [result, setResult] = useState<SQLQueryResult | null>(null)
  const [history, setHistory] = useState<any[]>([])

  useEffect(() => {
    loadHistory()
  }, [])

  const loadHistory = async () => {
    const data = await getQueryHistory()
    setHistory(data)
  }

  const handleExecute = async () => {
    if (!query.trim()) return
    
    setIsExecuting(true)
    try {
      const data = await executeNaturalLanguageQuery(query)
      setResult(data)
      toast.success('Query executed successfully')
      loadHistory()
    } catch (error) {
      toast.error('Failed to execute query')
    } finally {
      setIsExecuting(false)
    }
  }

  const handleExport = async () => {
    if (!result) return
    const blob = await exportQueryResultsToCSV(result)
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'query_results.csv'
    a.click()
    window.URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-6 h-full flex flex-col">
       {/* Header */}
       <div>
        <h1 className="text-2xl font-bold text-text-primary tracking-tight">Structured Query Interface</h1>
        <p className="text-text-secondary mt-1">
          Query the financial knowledge graph using natural language or SQL
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3 flex-1 min-h-0">
        
        {/* Left Panel: Query Input & History */}
        <div className="space-y-6 lg:col-span-1 flex flex-col">
          <Card className="bg-bg-card border-border-primary shrink-0">
            <CardHeader>
              <CardTitle className="text-base">Natural Language Query</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Textarea
                placeholder="e.g., Show me companies with highest dividend yields in the financial sector..."
                className="min-h-[120px] font-mono text-sm bg-bg-secondary border-border-secondary resize-none focus:border-accent-primary"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                    handleExecute()
                  }
                }}
              />
              <div className="flex justify-between items-center">
                 <span className="text-xs text-text-tertiary">Ctrl + Enter to run</span>
                 <Button 
                  onClick={handleExecute} 
                  disabled={isExecuting || !query.trim()}
                  className="bg-accent-primary text-bg-primary hover:bg-accent-secondary"
                >
                  {isExecuting ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Play className="h-4 w-4 mr-2" />}
                  Execute
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-bg-card border-border-primary flex-1 min-h-0 flex flex-col">
            <CardHeader className="pb-3 shrink-0">
               <div className="flex items-center gap-2">
                 <History className="h-4 w-4 text-accent-primary" />
                 <CardTitle className="text-base">Query History</CardTitle>
               </div>
            </CardHeader>
            <CardContent className="overflow-y-auto flex-1 pr-2 space-y-3">
              {history.map((item) => (
                <div 
                  key={item.id} 
                  className="p-3 rounded-lg bg-bg-secondary/50 border border-border-secondary hover:bg-bg-secondary hover:border-accent-primary/50 transition-colors cursor-pointer group"
                  onClick={() => setQuery(item.query)}
                >
                  <p className="text-sm text-text-primary line-clamp-2 group-hover:text-accent-primary font-medium">{item.query}</p>
                  <div className="flex items-center justify-between mt-2 text-xs text-text-tertiary">
                    <span className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {new Date(item.timestamp).toLocaleTimeString()}
                    </span>
                    <span className="font-mono">{item.executionTime}ms</span>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>

        {/* Right Panel: Results */}
        <div className="lg:col-span-2 flex flex-col min-h-0 space-y-6">
          
          {/* SQL Preview */}
          {result && (
             <Card className="bg-bg-card border-border-primary shrink-0">
               <CardHeader className="py-3 px-4 border-b border-border-primary/50 flex flex-row items-center justify-between">
                 <div className="flex items-center gap-2">
                   <FileCode className="h-4 w-4 text-accent-primary" />
                   <h3 className="text-sm font-semibold">Generated SQL</h3>
                 </div>
                 <Badge variant="outline" className="font-mono text-xs bg-success-primary/10 text-success-primary border-success-primary/20">
                   <CheckCircle2 className="h-3 w-3 mr-1" />
                   Valid
                 </Badge>
               </CardHeader>
               <CardContent className="p-0">
                 <SyntaxHighlighter
                    language="sql"
                    style={vscDarkPlus}
                    customStyle={{
                      margin: 0,
                      padding: '1rem',
                      fontSize: '0.875rem',
                      lineHeight: '1.5',
                      backgroundColor: 'transparent'
                    }}
                    wrapLongLines
                 >
                   {result.sql}
                 </SyntaxHighlighter>
               </CardContent>
             </Card>
          )}

          {/* Data Table */}
           <Card className="bg-bg-card border-border-primary flex-1 min-h-0 flex flex-col">
             <CardHeader className="py-3 px-4 border-b border-border-primary/50 shrink-0 flex flex-row items-center justify-between">
                <h3 className="text-sm font-semibold">
                  Results 
                  {result && <span className="ml-2 text-text-tertiary font-normal">({result.rowCount} rows)</span>}
                </h3>
                 {result && (
                  <Button variant="outline" size="sm" onClick={handleExport} className="h-8 gap-2">
                    <Download className="h-3.5 w-3.5" />
                    Export CSV
                  </Button>
                )}
             </CardHeader>
             <CardContent className="p-0 overflow-auto flex-1">
               {result ? (
                 <Table>
                   <TableHeader className="sticky top-0 bg-bg-card z-10">
                     <TableRow className="hover:bg-transparent border-border-secondary">
                       {result.columns.map((col, i) => (
                         <TableHead key={i} className="text-xs font-semibold text-text-secondary whitespace-nowrap h-9">
                           {col}
                         </TableHead>
                       ))}
                     </TableRow>
                   </TableHeader>
                   <TableBody>
                     {result.rows.map((row, i) => (
                       <TableRow key={i} className="hover:bg-bg-elevated/50 border-border-secondary/50">
                         {row.map((cell, j) => (
                           <TableCell key={j} className="py-2 text-sm text-text-primary whitespace-nowrap">
                             {cell}
                           </TableCell>
                         ))}
                       </TableRow>
                     ))}
                   </TableBody>
                 </Table>
               ) : (
                 <div className="h-full flex flex-col items-center justify-center text-text-tertiary p-8">
                   <div className="h-12 w-12 rounded-full bg-bg-secondary flex items-center justify-center mb-4">
                     <Play className="h-6 w-6 text-text-tertiary opacity-50" />
                   </div>
                   <p>Execute a query to see results</p>
                 </div>
               )}
             </CardContent>
           </Card>

        </div>
      </div>
    </div>
  )
}
