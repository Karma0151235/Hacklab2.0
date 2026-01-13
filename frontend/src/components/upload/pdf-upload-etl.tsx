'use client'

import { useState } from 'react'
import { FileUpload } from './file-upload'
import { Button } from '@/components/ui/button'
import { uploadPDFsForETL, getETLJobStatus, PDFProcessingStatus } from '@/lib/api/ingestion'
import { Loader2, CheckCircle2, XCircle, FileText, Database, Zap } from 'lucide-react'
import { cn } from '@/lib/utils'

interface UploadedFile {
  file: File
  status: 'pending' | 'uploaded' | 'processing' | 'completed' | 'failed'
}

export function PDFUploadWithETL() {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [jobId, setJobId] = useState<string | null>(null)
  const [jobStatus, setJobStatus] = useState<PDFProcessingStatus | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isPolling, setIsPolling] = useState(false)

  const handleFilesSelected = (files: File[]) => {
    const newFiles = files.map((file) => ({
      file,
      status: 'pending' as const,
    }))
    setUploadedFiles((prev) => [...prev, ...newFiles])
    setError(null)
  }

  const handleRemoveFile = (index: number) => {
    setUploadedFiles((prev) => prev.filter((_, i) => i !== index))
  }

  const handleStartETL = async () => {
    if (uploadedFiles.length === 0) {
      setError('No files to upload')
      return
    }

    setIsUploading(true)
    setError(null)

    try {
      // Upload files to ETL pipeline
      const files = uploadedFiles.map((uf) => uf.file)
      const response = await uploadPDFsForETL(files)

      setJobId(response.job_id)
      setUploadedFiles((prev) =>
        prev.map((uf) => ({ ...uf, status: 'uploaded' as const }))
      )

      // Start polling for status
      startPolling(response.job_id)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
      setIsUploading(false)
    }
  }

  const startPolling = async (jobIdToTrack: string) => {
    setIsPolling(true)

    const pollInterval = setInterval(async () => {
      try {
        const status = await getETLJobStatus(jobIdToTrack)
        setJobStatus(status)

        // Update file statuses based on job progress
        if (status.status === 'processing') {
          setUploadedFiles((prev) =>
            prev.map((uf) => ({ ...uf, status: 'processing' as const }))
          )
        }

        // Stop polling when complete or failed
        if (status.status === 'completed' || status.status === 'failed') {
          clearInterval(pollInterval)
          setIsPolling(false)
          setIsUploading(false)

          setUploadedFiles((prev) =>
            prev.map((uf) => ({
              ...uf,
              status: status.status === 'completed' ? 'completed' : 'failed',
            }))
          )
        }
      } catch (err) {
        console.error('Failed to fetch job status:', err)
        clearInterval(pollInterval)
        setIsPolling(false)
        setIsUploading(false)
        setError('Failed to track job status')
      }
    }, 2000) // Poll every 2 seconds

    // Cleanup on unmount
    return () => clearInterval(pollInterval)
  }

  const getStatusIcon = (status: UploadedFile['status']) => {
    switch (status) {
      case 'pending':
        return <FileText className="h-4 w-4 text-text-tertiary" />
      case 'uploaded':
      case 'processing':
        return <Loader2 className="h-4 w-4 animate-spin text-accent-primary" />
      case 'completed':
        return <CheckCircle2 className="h-4 w-4 text-success" />
      case 'failed':
        return <XCircle className="h-4 w-4 text-error" />
    }
  }

  const getProgressPercentage = () => {
    if (!jobStatus) return 0
    return Math.round((jobStatus.processed_files / jobStatus.total_files) * 100)
  }

  return (
    <div className="space-y-6">
      {/* File Upload Component */}
      <FileUpload
        onFilesSelected={handleFilesSelected}
        acceptedFileTypes={['.pdf']}
        maxFiles={20}
        maxSizeBytes={50 * 1024 * 1024}
      />

      {/* Uploaded Files List */}
      {uploadedFiles.length > 0 && (
        <div className="space-y-3">
          <h4 className="font-mono text-sm font-semibold text-text-primary">
            Selected Files ({uploadedFiles.length})
          </h4>

          <div className="space-y-2">
            {uploadedFiles.map((uploadedFile, index) => (
              <div
                key={index}
                className="flex items-center justify-between rounded-lg border border-border-secondary bg-bg-tertiary p-3"
              >
                <div className="flex items-center gap-3">
                  {getStatusIcon(uploadedFile.status)}
                  <div>
                    <p className="font-mono text-sm text-text-primary">
                      {uploadedFile.file.name}
                    </p>
                    <p className="font-mono text-xs text-text-tertiary">
                      {(uploadedFile.file.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                </div>

                {uploadedFile.status === 'pending' && (
                  <button
                    onClick={() => handleRemoveFile(index)}
                    className="text-text-tertiary transition-colors hover:text-error"
                  >
                    <XCircle className="h-4 w-4" />
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Progress Status */}
      {jobStatus && (
        <div className="rounded-lg border border-border-secondary bg-gradient-to-br from-bg-tertiary to-bg-secondary p-6">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h4 className="font-mono text-sm font-semibold text-text-primary">
                ETL Pipeline Status
              </h4>
              <p className="font-mono text-xs text-text-tertiary">Job ID: {jobId}</p>
            </div>
            <div
              className={cn(
                'rounded-full px-3 py-1 font-mono text-xs font-semibold',
                jobStatus.status === 'completed' && 'bg-success/20 text-success',
                jobStatus.status === 'processing' && 'bg-accent-primary/20 text-accent-primary',
                jobStatus.status === 'pending' && 'bg-text-tertiary/20 text-text-secondary',
                jobStatus.status === 'failed' && 'bg-error/20 text-error'
              )}
            >
              {jobStatus.status.toUpperCase()}
            </div>
          </div>

          {/* Progress Bar */}
          <div className="mb-4">
            <div className="mb-2 flex justify-between font-mono text-xs text-text-secondary">
              <span>
                Processing: {jobStatus.processed_files}/{jobStatus.total_files} files
              </span>
              <span>{getProgressPercentage()}%</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-bg-primary">
              <div
                className="h-full bg-gradient-to-r from-accent-primary to-accent-secondary transition-all duration-500"
                style={{ width: `${getProgressPercentage()}%` }}
              />
            </div>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-2 gap-4">
            <div className="flex items-center gap-2 rounded-lg bg-bg-primary/50 p-3">
              <Database className="h-5 w-5 text-accent-primary" />
              <div>
                <p className="font-mono text-xs text-text-tertiary">Text Chunks</p>
                <p className="font-mono text-lg font-semibold text-text-primary">
                  {jobStatus.text_chunks_loaded.toLocaleString()}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2 rounded-lg bg-bg-primary/50 p-3">
              <Database className="h-5 w-5 text-accent-secondary" />
              <div>
                <p className="font-mono text-xs text-text-tertiary">Table Chunks</p>
                <p className="font-mono text-lg font-semibold text-text-primary">
                  {jobStatus.table_chunks_loaded.toLocaleString()}
                </p>
              </div>
            </div>
          </div>

          {/* Errors */}
          {jobStatus.errors.length > 0 && (
            <div className="mt-4 rounded-lg border border-error/40 bg-error/5 p-3">
              <p className="mb-2 font-mono text-xs font-semibold text-error">
                Errors ({jobStatus.errors.length})
              </p>
              <div className="max-h-32 space-y-1 overflow-y-auto">
                {jobStatus.errors.map((err, idx) => (
                  <p key={idx} className="font-mono text-xs text-error/80">
                    • {err}
                  </p>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="rounded-lg border border-error/40 bg-error/5 p-4">
          <div className="flex items-start gap-3">
            <XCircle className="h-5 w-5 flex-shrink-0 text-error" />
            <div>
              <p className="font-sans text-sm font-semibold text-error">Upload Failed</p>
              <p className="mt-1 font-sans text-xs text-error/80">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Start ETL Button */}
      {uploadedFiles.length > 0 && !jobId && (
        <Button
          onClick={handleStartETL}
          disabled={isUploading}
          className="w-full gap-2 bg-gradient-to-r from-accent-primary to-accent-secondary font-mono font-semibold hover:opacity-90"
        >
          {isUploading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Uploading...
            </>
          ) : (
            <>
              <Zap className="h-4 w-4" />
              Start ETL Pipeline
            </>
          )}
        </Button>
      )}
    </div>
  )
}
