'use client'

import { PDFUploadWithETL } from '@/components/upload/pdf-upload-etl'
import { Upload as UploadIcon, Zap, Database, FileSearch } from 'lucide-react'

export default function UploadPage() {
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
                PDF ETL Pipeline
              </h1>
              <p className="font-sans text-base text-text-secondary">
                Upload PDFs for intelligent extraction, chunking, and vector embedding
              </p>
            </div>
          </div>
        </div>

        {/* PDF Upload with ETL Component */}
        <PDFUploadWithETL />

        {/* Info Box - Pipeline Stages */}
        <div className="rounded-lg border border-border-accent/20 bg-gradient-to-br from-bg-tertiary to-bg-secondary p-6">
          <h3 className="mb-6 font-sans text-lg font-semibold text-text-primary">
            ETL Pipeline Stages
          </h3>
          
          <div className="grid gap-4 md:grid-cols-3">
            {/* Stage 1: Extract */}
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent-primary/20">
                  <FileSearch className="h-4 w-4 text-accent-primary" />
                </div>
                <h4 className="font-mono text-sm font-semibold text-text-primary">
                  1. Extract
                </h4>
              </div>
              <ul className="space-y-2 font-sans text-sm text-text-secondary">
                <li className="flex items-start gap-2">
                  <span className="mt-1 flex h-1.5 w-1.5 flex-shrink-0 rounded-full bg-accent-primary" />
                  <span>Parse PDF text using pdfplumber</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-1 flex h-1.5 w-1.5 flex-shrink-0 rounded-full bg-accent-primary" />
                  <span>Extract tables using tabula-py</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-1 flex h-1.5 w-1.5 flex-shrink-0 rounded-full bg-accent-primary" />
                  <span>Identify company metadata</span>
                </li>
              </ul>
            </div>

            {/* Stage 2: Transform */}
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent-secondary/20">
                  <Zap className="h-4 w-4 text-accent-secondary" />
                </div>
                <h4 className="font-mono text-sm font-semibold text-text-primary">
                  2. Transform
                </h4>
              </div>
              <ul className="space-y-2 font-sans text-sm text-text-secondary">
                <li className="flex items-start gap-2">
                  <span className="mt-1 flex h-1.5 w-1.5 flex-shrink-0 rounded-full bg-accent-secondary" />
                  <span>Chunk text (500 chars, 50 overlap)</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-1 flex h-1.5 w-1.5 flex-shrink-0 rounded-full bg-accent-secondary" />
                  <span>Generate vector embeddings</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-1 flex h-1.5 w-1.5 flex-shrink-0 rounded-full bg-accent-secondary" />
                  <span>Process table data</span>
                </li>
              </ul>
            </div>

            {/* Stage 3: Load */}
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-success/20">
                  <Database className="h-4 w-4 text-success" />
                </div>
                <h4 className="font-mono text-sm font-semibold text-text-primary">
                  3. Load
                </h4>
              </div>
              <ul className="space-y-2 font-sans text-sm text-text-secondary">
                <li className="flex items-start gap-2">
                  <span className="mt-1 flex h-1.5 w-1.5 flex-shrink-0 rounded-full bg-success" />
                  <span>Insert into MilvusDB</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-1 flex h-1.5 w-1.5 flex-shrink-0 rounded-full bg-success" />
                  <span>Index for semantic search</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="mt-1 flex h-1.5 w-1.5 flex-shrink-0 rounded-full bg-success" />
                  <span>Ready for Copilot queries</span>
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* Technical Info */}
        <div className="rounded-lg border border-border-secondary bg-bg-tertiary p-4">
          <p className="mb-2 font-mono text-xs font-semibold uppercase tracking-wider text-text-tertiary">
            Technical Details
          </p>
          <div className="grid gap-3 md:grid-cols-2">
            <div>
              <p className="font-mono text-xs text-text-secondary">
                <span className="text-accent-primary">Embedding Model:</span>{' '}
                sentence-transformers/all-MiniLM-L6-v2
              </p>
            </div>
            <div>
              <p className="font-mono text-xs text-text-secondary">
                <span className="text-accent-primary">Vector DB:</span> MilvusDB
                (localhost:19639)
              </p>
            </div>
            <div>
              <p className="font-mono text-xs text-text-secondary">
                <span className="text-accent-primary">Collections:</span> pdf_text_chunks,
                pdf_table_chunks
              </p>
            </div>
            <div>
              <p className="font-mono text-xs text-text-secondary">
                <span className="text-accent-primary">Embedding Dim:</span> 384
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
