'use client'

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts'

interface FinancialChartProps {
  data: any[]
  series: {
    key: string
    name: string
    color: string
    strokeWidth?: number
    dot?: boolean
  }[]
  formatter?: (value: number) => string
}

export function FinancialChart({ data, series, formatter }: FinancialChartProps) {
  return (
    <div className="w-full h-full min-h-[300px]">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#1f2937" />
          <XAxis 
            dataKey="period" 
            stroke="#6b7280" 
            tick={{ fontSize: 11, fill: '#6b7280' }}
            tickLine={false}
            axisLine={false}
            dy={10}
          />
          <YAxis 
            stroke="#6b7280"
            tick={{ fontSize: 11, fill: '#6b7280' }}
            tickLine={false}
            axisLine={false}
            tickFormatter={formatter}
          />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: '#111827', 
              borderColor: '#374151',
              fontSize: '12px',
              color: '#f3f4f6'
            }}
            itemStyle={{ fontSize: '12px' }}
            labelStyle={{ color: '#9ca3af', marginBottom: '4px' }}
          />
          <Legend 
            wrapperStyle={{ paddingTop: '20px' }}
            formatter={(value) => <span className="text-xs text-gray-400 font-mono">{value}</span>}
          />
          {series.map((s) => (
            <Line
              key={s.key}
              type="monotone"
              dataKey={s.key}
              name={s.name}
              stroke={s.color}
              strokeWidth={s.strokeWidth || 2}
              dot={s.dot ?? false}
              activeDot={{ r: 4, strokeWidth: 0 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
