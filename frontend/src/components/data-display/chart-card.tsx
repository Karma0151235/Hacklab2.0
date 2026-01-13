'use client'

import { Card } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Button } from '@/components/ui/button'
import { Download, Maximize2 } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ChartCardProps {
  title: string
  subtitle?: string
  children: React.ReactNode
  className?: string
  period?: string
  onPeriodChange?: (period: string) => void
}

export function ChartCard({
  title,
  subtitle,
  children,
  className,
  period = '1Y',
  onPeriodChange
}: ChartCardProps) {
  return (
    <Card className={cn(
      "flex flex-col h-full bg-bg-card border-border-primary",
      "hover:border-accent-primary/50 transition-colors duration-300",
      className
    )}>
      <div className="flex items-center justify-between p-4 border-b border-border-primary/50">
        <div>
          <h3 className="text-sm font-semibold text-text-primary tracking-tight">{title}</h3>
          {subtitle && (
            <p className="text-xs text-text-tertiary mt-0.5">{subtitle}</p>
          )}
        </div>
        
        <div className="flex items-center gap-2">
          {onPeriodChange && (
            <Select value={period} onValueChange={onPeriodChange}>
              <SelectTrigger className="h-7 w-[80px] text-xs bg-bg-secondary border-border-secondary">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1Q">1Q</SelectItem>
                <SelectItem value="1Y">1Y</SelectItem>
                <SelectItem value="3Y">3Y</SelectItem>
                <SelectItem value="5Y">5Y</SelectItem>
                <SelectItem value="ALL">All</SelectItem>
              </SelectContent>
            </Select>
          )}
          
          <Button
            variant="ghost" 
            size="icon"
            className="h-7 w-7 text-text-tertiary hover:text-accent-primary hover:bg-accent-primary/10"
          >
            <Download className="h-3.5 w-3.5" />
          </Button>

           <Button
            variant="ghost" 
            size="icon"
            className="h-7 w-7 text-text-tertiary hover:text-accent-primary hover:bg-accent-primary/10"
          >
            <Maximize2 className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>
      
      <div className="flex-1 p-4 min-h-[300px]">
        {children}
      </div>
    </Card>
  )
}
