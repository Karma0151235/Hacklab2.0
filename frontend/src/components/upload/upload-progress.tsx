'use client'

import { CheckCircle2, XCircle, Loader2, X } from 'lucide-react'
import { cn } from '@/lib/utils'

export interface UploadProgress {
  fileId: string
  fileName: string
  fileSize: number
  progress: number
  status: 'pending' | 'uploading' | 'completed' | 'error'
  errorMessage?: string
}

interface UploadProgressProps {
  uploads: UploadProgress[]
  onCancel?: (fileId: string) => void
  className?: string
}

export function UploadProgressDisplay({
  uploads,
  onCancel,
  className,
}: UploadProgressProps) {
  if (uploads.length === 0) return null

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  return (
    <div className={cn('space-y-3', className)}>
      {uploads.map((upload) => (
        <div
          key={upload.fileId}
          className="rounded-lg border border-border-secondary bg-gradient-to-br from-bg-tertiary to-bg-secondary p-4"
        >
          {/* Header */}
          <div className="mb-3 flex items-start justify-between gap-3">
            <div className="flex-1 min-w-0">
              <p className="truncate font-sans text-sm font-semibold text-text-primary">
                {upload.fileName}
              </p>
              <p className="font-mono text-xs text-text-tertiary">
                {formatFileSize(upload.fileSize)}
              </p>
            </div>

            {/* Status Icon */}
            <div className="flex-shrink-0">
              {upload.status === 'uploading' && (
                <Loader2 className="h-5 w-5 animate-spin text-accent-primary" />
              )}
              {upload.status === 'completed' && (
                <CheckCircle2 className="h-5 w-5 text-success" />
              )}
              {upload.status === 'error' && (
                <XCircle className="h-5 w-5 text-error" />
              )}
              {upload.status === 'pending' && (
                <div className="h-5 w-5 rounded-full border-2 border-border-secondary" />
              )}
            </div>
          </div>

          {/* Progress Bar */}
          {(upload.status === 'uploading' || upload.status === 'pending') && (
            <div className="mb-3">
              <div className="mb-2 flex items-center justify-between">
                <span className="font-mono text-xs font-semibold text-text-tertiary">
                  {upload.status === 'pending' ? 'Waiting...' : 'Uploading...'}
                </span>
                <span className="font-mono text-xs font-bold text-accent-primary">
                  {upload.progress}%
                </span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-bg-primary">
                <div
                  className="h-full rounded-full bg-accent-primary transition-all duration-300"
                  style={{ width: `${upload.progress}%` }}
                />
              </div>
            </div>
          )}

          {/* Error Message */}
          {upload.status === 'error' && upload.errorMessage && (
            <div className="mb-3 rounded-md bg-error/5 p-3">
              <p className="font-sans text-xs text-error">
                {upload.errorMessage}
              </p>
            </div>
          )}

          {/* Success Message */}
          {upload.status === 'completed' && (
            <div className="mb-3 rounded-md bg-success/5 p-3">
              <p className="font-sans text-xs text-success">
                Upload completed successfully
              </p>
            </div>
          )}

          {/* Cancel Button */}
          {(upload.status === 'uploading' || upload.status === 'pending') &&
            onCancel && (
              <div className="flex justify-end">
                <button
                  onClick={() => onCancel(upload.fileId)}
                  className="flex items-center gap-1.5 rounded-md border border-border-secondary bg-bg-elevated px-3 py-1.5 font-mono text-xs font-semibold text-text-secondary transition-all hover:border-error/40 hover:text-error"
                >
                  <X className="h-3.5 w-3.5" />
                  <span>Cancel</span>
                </button>
              </div>
            )}
        </div>
      ))}
    </div>
  )
}
