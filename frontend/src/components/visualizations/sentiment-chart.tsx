'use client'

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceDot,
  Area,
  AreaChart
} from 'recharts'

interface SentimentDataPoint {
  date: string
  score: number // -100 to 100 or -1 to 1
  event?: string
}

interface SentimentChartProps {
  data: SentimentDataPoint[]
}

export function SentimentChart({ data }: SentimentChartProps) {
  // Calculate gradient offset for red/green split based on data range if needed
  // For now using a visual gradient

  return (
    <div className="w-full h-full min-h-[300px]">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 20, right: 30, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="sentimentGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
            </linearGradient>
             <linearGradient id="lineGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#10b981" />
              <stop offset="50%" stopColor="#f59e0b" />
              <stop offset="100%" stopColor="#ef4444" />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#1f2937" />
          <XAxis 
            dataKey="date" 
            stroke="#6b7280"
            tick={{ fontSize: 11, fill: '#6b7280' }}
            tickLine={false}
            axisLine={false}
            dy={10}
          />
          <YAxis 
            domain={[-1, 1]} 
            stroke="#6b7280"
            tick={{ fontSize: 11, fill: '#6b7280' }}
            tickLine={false}
            axisLine={false}
          />
          <Tooltip 
             contentStyle={{ 
              backgroundColor: '#111827', 
              borderColor: '#374151',
              fontSize: '12px',
              color: '#f3f4f6'
            }}
            labelStyle={{ color: '#9ca3af' }}
          />
          <Area
            type="monotone"
            dataKey="score"
            stroke="#06b6d4"
            fill="url(#sentimentGradient)"
            strokeWidth={2}
          />
           {/* Event markers */}
          {data.filter(d => d.event).map((d, i) => (
             <ReferenceDot 
                key={i} 
                x={d.date} 
                y={d.score} 
                r={4} 
                fill="#fff" 
                stroke="#06b6d4"
                strokeWidth={2}
             />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
