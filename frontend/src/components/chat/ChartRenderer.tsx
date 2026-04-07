"use client"

import React, { useMemo } from 'react'
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts'
import { BarChart3, LineChart as LineChartIcon, PieChart as PieChartIcon } from 'lucide-react'

interface ChartData {
  type: 'bar' | 'line' | 'pie'
  data: any[]
  xAxis?: string
  yAxis?: string
  is_chart_data: boolean
  title?: string
}

const COLORS = ['#2D2D2D', '#D95D39', '#F0A202', '#3E5C76', '#778DA9']

export function ChartRenderer({ jsonString }: { jsonString: string }) {
  const chartData = useMemo(() => {
    try {
      const parsed = JSON.parse(jsonString)
      if (parsed && parsed.is_chart_data && Array.isArray(parsed.data)) {
        return parsed as ChartData
      }
    } catch (e) {
      console.error('Failed to parse chart JSON', e)
    }
    return null
  }, [jsonString])

  if (!chartData) return null

  const { type, data, xAxis, yAxis, title } = chartData

  return (
    <div className="w-full bg-white rounded-2xl border border-beige p-6 my-6 shadow-sm overflow-hidden animate-in fade-in slide-in-from-bottom-2 duration-500">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          {type === 'bar' && <BarChart3 className="w-4 h-4 text-accent-terra" />}
          {type === 'line' && <LineChartIcon className="w-4 h-4 text-accent-terra" />}
          {type === 'pie' && <PieChartIcon className="w-4 h-4 text-accent-terra" />}
          <span className="text-sm font-semibold text-charcoal italic font-display">
            {title || 'AI Generated Insights'}
          </span>
        </div>
      </div>

      <div className="h-[300px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          {type === 'bar' ? (
            <BarChart data={data}>
              <XAxis 
                dataKey={xAxis} 
                axisLine={false} 
                tickLine={false} 
                tick={{ fontSize: 10, fill: '#6B7280' }} 
              />
              <YAxis 
                axisLine={false} 
                tickLine={false} 
                tick={{ fontSize: 10, fill: '#6B7280' }} 
              />
              <Tooltip 
                contentStyle={{ 
                  borderRadius: '12px', 
                  border: '1px solid #F5F5DC', 
                  boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
                  fontSize: '12px'
                }} 
              />
              <Bar 
                dataKey={yAxis} 
                fill="#2D2D2D" 
                radius={[4, 4, 0, 0]} 
              />
            </BarChart>
          ) : type === 'line' ? (
            <LineChart data={data}>
              <XAxis 
                dataKey={xAxis} 
                axisLine={false} 
                tickLine={false} 
                tick={{ fontSize: 10, fill: '#6B7280' }} 
              />
              <YAxis 
                axisLine={false} 
                tickLine={false} 
                tick={{ fontSize: 10, fill: '#6B7280' }} 
              />
              <Tooltip 
                contentStyle={{ 
                  borderRadius: '12px', 
                  border: '1px solid #F5F5DC', 
                  boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
                  fontSize: '12px'
                }} 
              />
              <Line 
                type="monotone" 
                dataKey={yAxis} 
                stroke="#D95D39" 
                strokeWidth={3} 
                dot={{ r: 4, fill: '#D95D39', strokeWidth: 0 }} 
                activeDot={{ r: 6 }}
              />
            </LineChart>
          ) : (
            <PieChart>
              <Pie
                data={data}
                innerRadius={60}
                outerRadius={80}
                paddingAngle={5}
                dataKey={yAxis}
                nameKey={xAxis}
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip 
                contentStyle={{ 
                  borderRadius: '12px', 
                  border: '1px solid #F5F5DC', 
                  boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
                  fontSize: '12px'
                }} 
              />
              <Legend verticalAlign="bottom" height={36} iconType="circle" wrapperStyle={{ fontSize: '10px' }} />
            </PieChart>
          )}
        </ResponsiveContainer>
      </div>
    </div>
  )
}
