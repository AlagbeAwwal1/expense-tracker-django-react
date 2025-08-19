import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts'
import { CATEGORY_COLORS, COLORS } from '@/lib/colors'
import { fmtCur } from '@/lib/format'

export default function MonthlyBarCard({ data, categoryKeys }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Monthly Breakdown</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-80">
          <ResponsiveContainer>
            <BarChart data={data} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis tickFormatter={(v)=>fmtCur.format(v)} />
              <Tooltip formatter={(v)=>fmtCur.format(v)} />
              <Legend />
              {categoryKeys.map((k, i) => (
                <Bar
                  key={k}
                  dataKey={k}
                  stackId="spend"
                  fill={CATEGORY_COLORS[k] || COLORS[i % COLORS.length]}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}
