'use client'

import { useState } from 'react'
import { Download, ZoomIn, ZoomOut, ChevronLeft, ChevronRight, ExternalLink } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'

interface PDFViewerProps {
  url: string
  title?: string
  highlightPage?: number
}

export function PDFViewer({ url, title, highlightPage = 1 }: PDFViewerProps) {
  const [currentPage, setCurrentPage] = useState(highlightPage)
  const [zoom, setZoom] = useState(100)
  const [totalPages] = useState(12) // Mock total pages

  const handleZoomIn = () => setZoom(prev => Math.min(prev + 25, 200))
  const handleZoomOut = () => setZoom(prev => Math.max(prev - 25, 50))
  const handlePrevPage = () => setCurrentPage(prev => Math.max(prev - 1, 1))
  const handleNextPage = () => setCurrentPage(prev => Math.min(prev + 1, totalPages))

  return (
    <Card className="bg-gradient-to-br from-bg-elevated to-bg-secondary border-border-primary overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border-primary bg-bg-tertiary/50">
        <div className="flex items-center gap-3">
          <h3 className="font-mono text-sm text-text-primary font-medium">
            {title || 'PDF Document'}
          </h3>
          <span className="text-xs text-text-tertiary font-mono">
            Page {currentPage} / {totalPages}
          </span>
        </div>

        <div className="flex items-center gap-2">
          {/* Zoom Controls */}
          <div className="flex items-center gap-1 px-2 py-1 bg-bg-secondary rounded-md border border-border-secondary">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleZoomOut}
              disabled={zoom <= 50}
              className="h-7 w-7 p-0 hover:bg-bg-elevated"
            >
              <ZoomOut className="h-3.5 w-3.5" />
            </Button>
            <span className="text-xs font-mono text-text-secondary w-12 text-center">
              {zoom}%
            </span>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleZoomIn}
              disabled={zoom >= 200}
              className="h-7 w-7 p-0 hover:bg-bg-elevated"
            >
              <ZoomIn className="h-3.5 w-3.5" />
            </Button>
          </div>

          {/* Action Buttons */}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => window.open(url, '_blank')}
            className="h-8 gap-1.5 text-text-secondary hover:text-accent-primary hover:bg-bg-elevated"
          >
            <ExternalLink className="h-3.5 w-3.5" />
            <span className="text-xs font-mono">Open</span>
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              // Mock download
              const a = document.createElement('a')
              a.href = url
              a.download = title || 'document.pdf'
              a.click()
            }}
            className="h-8 gap-1.5 text-text-secondary hover:text-accent-primary hover:bg-bg-elevated"
          >
            <Download className="h-3.5 w-3.5" />
            <span className="text-xs font-mono">Download</span>
          </Button>
        </div>
      </div>

      {/* PDF Preview Area */}
      <div className="relative bg-bg-primary p-6 flex items-center justify-center min-h-[600px]">
        {/* Mock PDF Preview */}
        <div 
          className="bg-white shadow-2xl transition-transform duration-200"
          style={{ 
            transform: `scale(${zoom / 100})`,
            transformOrigin: 'center top',
            width: '612px', // A4 width
            minHeight: '792px', // A4 height
          }}
        >
          <div className="p-12 space-y-4">
            {/* Mock PDF Content */}
            <div className="text-center mb-8">
              <div className="text-2xl font-bold text-gray-900 mb-2">
                {title || 'Financial Document'}
              </div>
              <div className="text-sm text-gray-600">Page {currentPage}</div>
            </div>
            
            {currentPage === highlightPage && (
              <div className="border-2 border-yellow-400 bg-yellow-50 p-4 rounded">
                <div className="text-sm font-semibold text-gray-900 mb-2">
                  Highlighted Section
                </div>
                <div className="text-sm text-gray-700 leading-relaxed">
                  This is a highlighted section of the document that was referenced
                  in the analysis. The content shown here demonstrates key financial
                  metrics and important disclosures relevant to the alert or query.
                </div>
              </div>
            )}

            <div className="space-y-3 text-gray-700 text-sm leading-relaxed">
              <p>
                Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod
                tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam,
                quis nostrud exercitation ullamco laboris.
              </p>
              <p>
                Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore
                eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident.
              </p>
              <div className="border-l-4 border-gray-300 pl-4 py-2 my-4 bg-gray-50">
                <div className="text-xs font-semibold text-gray-600 mb-1">NOTE</div>
                <div className="text-sm text-gray-700">
                  Important financial disclosure or regulatory requirement noted in this section.
                </div>
              </div>
              <p>
                Sunt in culpa qui officia deserunt mollit anim id est laborum. Sed ut
                perspiciatis unde omnis iste natus error sit voluptatem accusantium.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Controls */}
      <div className="flex items-center justify-center gap-2 p-4 border-t border-border-primary bg-bg-tertiary/50">
        <Button
          variant="ghost"
          size="sm"
          onClick={handlePrevPage}
          disabled={currentPage <= 1}
          className="h-8 gap-1.5 text-text-secondary hover:text-accent-primary hover:bg-bg-elevated disabled:opacity-30"
        >
          <ChevronLeft className="h-4 w-4" />
          <span className="text-xs font-mono">Previous</span>
        </Button>
        
        <div className="flex items-center gap-1">
          <input
            type="number"
            value={currentPage}
            onChange={(e) => {
              const page = parseInt(e.target.value)
              if (page >= 1 && page <= totalPages) {
                setCurrentPage(page)
              }
            }}
            className="w-12 h-8 text-center bg-bg-secondary border border-border-secondary rounded text-xs font-mono text-text-primary focus:outline-none focus:border-accent-primary"
            min={1}
            max={totalPages}
          />
          <span className="text-xs text-text-tertiary font-mono">of {totalPages}</span>
        </div>

        <Button
          variant="ghost"
          size="sm"
          onClick={handleNextPage}
          disabled={currentPage >= totalPages}
          className="h-8 gap-1.5 text-text-secondary hover:text-accent-primary hover:bg-bg-elevated disabled:opacity-30"
        >
          <span className="text-xs font-mono">Next</span>
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </Card>
  )
}
