'use client'

import { useState } from 'react'
import { FileUpload } from '@/components/upload/file-upload'
import {
  UploadProgressDisplay,
  type UploadProgress,
} from '@/components/upload/upload-progress'
import { Upload as UploadIcon, CheckCircle2 } from 'lucide-react'

export default function UploadPage() {
  const [uploads, setUploads] = useState<UploadProgress[]>([])

  const handleFilesSelected = (files: File[]) => {
    // Create upload progress entries
    const newUploads: UploadProgress[] = files.map((file) => ({
      fileId: `${Date.now()}-${file.name}`,
      fileName: file.name,
      fileSize: file.size,
      progress: 0,
      status: 'pending' as const,
    }))

    setUploads((prev) => [...prev, ...newUploads])

    // Simulate upload for each file
    newUploads.forEach((upload, index) => {
      setTimeout(() => {
        simulateUpload(upload.fileId)
      }, index * 100) // Stagger the start
    })
  }

  const simulateUpload = (fileId: string) => {
    // Update status to uploading
    setUploads((prev) =>
      prev.map((u) =>
        u.fileId === fileId ? { ...u, status: 'uploading' as const } : u
      )
    )

    // Simulate progress
    let progress = 0
    const interval = setInterval(() => {
      progress += Math.random() * 15
      if (progress >= 100) {
        progress = 100
        clearInterval(interval)

        // Mark as completed
        setUploads((prev) =>
          prev.map((u) =>
            u.fileId === fileId
              ? { ...u, progress: 100, status: 'completed' as const }
              : u
          )
        )
      } else {
        setUploads((prev) =>
          prev.map((u) =>
            u.fileId === fileId ? { ...u, progress: Math.round(progress) } : u
          )
        )
      }
    }, 300)
  }

  const handleCancelUpload = (fileId: string) => {
    setUploads((prev) =>
      prev.map((u) =>
        u.fileId === fileId
          ? {
              ...u,
              status: 'error' as const,
              errorMessage: 'Upload cancelled by user',
            }
          : u
      )
    )
  }

  const completedCount = uploads.filter((u) => u.status === 'completed').length
  const uploadingCount = uploads.filter(
    (u) => u.status === 'uploading' || u.status === 'pending'
  ).length
  const errorCount = uploads.filter((u) => u.status === 'error').length

  return (
    <div className="min-h-screen bg-gradient-to-br from-bg-primary via-bg-secondary to-bg-primary p-8">
      <div className="mx-auto max-w-5xl space-y-8">
        {/* Page Header */}
        <div className="mb-8">
          <div className="mb-4 flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-accent-primary/10">
              <UploadIcon className="h-6 w-6 text-accent-primary" />
            </div>
            <div>
              <h1 className="font-sans text-4xl font-bold text-text-primary">
                Upload Documents
              </h1>
              <p className="font-sans text-base text-text-secondary">
                Manually ingest PDFs and CSV files for analysis
              </p>
            </div>
          </div>

          {/* Stats */}
          {uploads.length > 0 && (
            <div className="grid grid-cols-3 gap-4">
              <div className="rounded-lg border border-border-secondary bg-bg-tertiary p-4">
                <p className="mb-1 font-mono text-xs font-semibold uppercase tracking-wider text-text-tertiary">
                  Uploading
                </p>
                <p className="font-mono text-2xl font-bold text-accent-primary">
                  {uploadingCount}
                </p>
              </div>

              <div className="rounded-lg border border-border-secondary bg-bg-tertiary p-4">
                <p className="mb-1 font-mono text-xs font-semibold uppercase tracking-wider text-text-tertiary">
                  Completed
                </p>
                <p className="font-mono text-2xl font-bold text-success">
                  {completedCount}
                </p>
              </div>

              <div className="rounded-lg border border-border-secondary bg-bg-tertiary p-4">
                <p className="mb-1 font-mono text-xs font-semibold uppercase tracking-wider text-text-tertiary">
                  Errors
                </p>
                <p className="font-mono text-2xl font-bold text-error">
                  {errorCount}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Upload Area */}
        <FileUpload onFilesSelected={handleFilesSelected} />

        {/* Upload Progress */}
        {uploads.length > 0 && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="font-sans text-2xl font-bold text-text-primary">
                Upload Queue
              </h2>
              {completedCount === uploads.length && uploads.length > 0 && (
                <div className="flex items-center gap-2 text-success">
                  <CheckCircle2 className="h-5 w-5" />
                  <span className="font-mono text-sm font-semibold">
                    All uploads completed
                  </span>
                </div>
              )}
            </div>

            <UploadProgressDisplay
              uploads={uploads}
              onCancel={handleCancelUpload}
            />
          </div>
        )}

        {/* Info Box */}
        <div className="rounded-lg border border-border-accent/20 bg-gradient-to-br from-bg-tertiary to-bg-secondary p-6">
          <h3 className="mb-3 font-sans text-lg font-semibold text-text-primary">
            What happens after upload?
          </h3>
          <ul className="space-y-2 font-sans text-sm text-text-secondary">
            <li className="flex items-start gap-2">
              <span className="mt-1 flex h-1.5 w-1.5 flex-shrink-0 rounded-full bg-accent-primary" />
              <span>
                Documents are processed through our AI pipeline for entity
                extraction and analysis
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="mt-1 flex h-1.5 w-1.5 flex-shrink-0 rounded-full bg-accent-primary" />
              <span>
                Text content is indexed and made searchable through Copilot
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="mt-1 flex h-1.5 w-1.5 flex-shrink-0 rounded-full bg-accent-primary" />
              <span>
                Financial tables are extracted and added to the analytics
                database
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="mt-1 flex h-1.5 w-1.5 flex-shrink-0 rounded-full bg-accent-primary" />
              <span>
                Compliance alerts are automatically generated if any issues are
                detected
              </span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  )
}
