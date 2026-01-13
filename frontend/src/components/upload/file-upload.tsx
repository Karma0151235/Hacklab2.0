'use client'

import { useCallback, useState } from 'react'
import { Upload, FileText, X } from 'lucide-react'
import { cn } from '@/lib/utils'

interface FileUploadProps {
  onFilesSelected: (files: File[]) => void
  acceptedFileTypes?: string[]
  maxFiles?: number
  maxSizeBytes?: number
  className?: string
}

export function FileUpload({
  onFilesSelected,
  acceptedFileTypes = ['.pdf', '.csv'],
  maxFiles = 10,
  maxSizeBytes = 50 * 1024 * 1024, // 50MB
  className,
}: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const validateFiles = (files: File[]): { valid: File[]; error?: string } => {
    if (files.length > maxFiles) {
      return {
        valid: [],
        error: `Maximum ${maxFiles} files allowed`,
      }
    }

    const validFiles: File[] = []
    const invalidFiles: string[] = []

    files.forEach((file) => {
      const extension = `.${file.name.split('.').pop()?.toLowerCase()}`
      const isValidType = acceptedFileTypes.some((type) =>
        extension === type.toLowerCase()
      )

      if (!isValidType) {
        invalidFiles.push(`${file.name} (unsupported type)`)
        return
      }

      if (file.size > maxSizeBytes) {
        invalidFiles.push(
          `${file.name} (exceeds ${Math.round(maxSizeBytes / 1024 / 1024)}MB)`
        )
        return
      }

      validFiles.push(file)
    })

    if (invalidFiles.length > 0) {
      return {
        valid: validFiles,
        error: `Invalid files: ${invalidFiles.join(', ')}`,
      }
    }

    return { valid: validFiles }
  }

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }, [])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
  }, [])

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      e.stopPropagation()
      setIsDragging(false)
      setError(null)

      const files = Array.from(e.dataTransfer.files)
      const { valid, error } = validateFiles(files)

      if (error) {
        setError(error)
      }

      if (valid.length > 0) {
        onFilesSelected(valid)
      }
    },
    [onFilesSelected, acceptedFileTypes, maxFiles, maxSizeBytes]
  )

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setError(null)

      if (!e.target.files) return

      const files = Array.from(e.target.files)
      const { valid, error } = validateFiles(files)

      if (error) {
        setError(error)
      }

      if (valid.length > 0) {
        onFilesSelected(valid)
      }

      // Reset input
      e.target.value = ''
    },
    [onFilesSelected, acceptedFileTypes, maxFiles, maxSizeBytes]
  )

  return (
    <div className={cn('space-y-4', className)}>
      {/* Drop Zone */}
      <div
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        className={cn(
          'relative rounded-lg border-2 border-dashed transition-all',
          isDragging
            ? 'border-accent-primary bg-accent-primary/5'
            : 'border-border-secondary bg-gradient-to-br from-bg-tertiary to-bg-secondary hover:border-accent-primary/40'
        )}
      >
        <div className="p-12">
          {/* Upload Icon */}
          <div className="mb-6 flex justify-center">
            <div
              className={cn(
                'flex h-20 w-20 items-center justify-center rounded-2xl transition-colors',
                isDragging
                  ? 'bg-accent-primary/20'
                  : 'bg-accent-primary/10'
              )}
            >
              <Upload
                className={cn(
                  'h-10 w-10 transition-colors',
                  isDragging ? 'text-accent-primary' : 'text-accent-primary'
                )}
              />
            </div>
          </div>

          {/* Text */}
          <div className="mb-6 text-center">
            <h3 className="mb-2 font-sans text-lg font-semibold text-text-primary">
              {isDragging ? 'Drop files here' : 'Upload Files'}
            </h3>
            <p className="mb-4 font-sans text-sm text-text-secondary">
              Drag and drop your files here, or click to browse
            </p>
            <p className="font-mono text-xs text-text-tertiary">
              Supported formats: {acceptedFileTypes.join(', ')} • Max{' '}
              {Math.round(maxSizeBytes / 1024 / 1024)}MB per file
            </p>
          </div>

          {/* Browse Button */}
          <div className="flex justify-center">
            <label className="cursor-pointer">
              <input
                type="file"
                multiple
                accept={acceptedFileTypes.join(',')}
                onChange={handleFileInput}
                className="hidden"
              />
              <div className="flex items-center gap-2 rounded-lg bg-accent-primary px-6 py-3 font-mono text-sm font-semibold text-bg-primary transition-all hover:bg-accent-secondary">
                <FileText className="h-4 w-4" />
                <span>Browse Files</span>
              </div>
            </label>
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="flex items-start gap-3 rounded-lg border border-error/40 bg-error/5 p-4">
          <div className="flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-error/20">
            <X className="h-3 w-3 text-error" />
          </div>
          <div className="flex-1">
            <p className="font-sans text-sm font-semibold text-error">
              Upload Error
            </p>
            <p className="mt-1 font-sans text-xs text-error/80">{error}</p>
          </div>
          <button
            onClick={() => setError(null)}
            className="text-error/60 hover:text-error"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}
    </div>
  )
}
