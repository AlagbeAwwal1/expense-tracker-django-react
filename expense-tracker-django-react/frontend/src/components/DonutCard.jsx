import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { PieChart, Pie, Tooltip, Cell, ResponsiveContainer, Legend } from 'recharts'
import { CATEGORY_COLORS, COLORS } from '@/lib/colors'
import { fmtCur } from '@/lib/format'

export default function DonutCard({ data }) {
const spendOnly = data.filter(d => d.category !== 'Income')
const total = spendOnly.reduce((a,x)=>a + (x.amount||0), 0)


  return (
    <Card>
      <CardHeader>
        <CardTitle>Spend by Category</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-64">
          <ResponsiveContainer>
            <PieChart>
              <Pie
                dataKey="amount"
                data={spendOnly}
                nameKey="category"
                innerRadius={60}
                outerRadius={100}
                label={({ name, percent }) => `${name} ${(percent*100).toFixed(0)}%`}
              >
                {data.map((x, i) => (
                  <Cell key={i} fill={CATEGORY_COLORS[x.category] || COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(v) => fmtCur.format(v)} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="mt-2 font-semibold text-slate-700">Total: {fmtCur.format(total)}</div>
      </CardContent>
    </Card>
  )
}
