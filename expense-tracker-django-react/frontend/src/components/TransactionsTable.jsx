import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow
} from '@/components/ui/table'
import { Input } from '@/components/ui/input'
import { fmtCur } from '@/lib/format'

export default function TransactionsTable({ txs, onUpdateCat }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Transactions</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Date</TableHead>
                <TableHead>Merchant</TableHead>
                <TableHead>Description</TableHead>
                <TableHead>Amount</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Category</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {txs.map((t) => (
                <TableRow key={t.id}>
                  <TableCell>{t.date}</TableCell>
                  <TableCell>{t.merchant}</TableCell>
                  <TableCell className="max-w-[360px] truncate">{t.description}</TableCell>
                  <TableCell>{fmtCur.format(Number(t.amount) || 0)}</TableCell>
                  <TableCell>{t.type}</TableCell>
                  <TableCell>
                    <Input
                      defaultValue={t.category}
                      onBlur={(e)=>onUpdateCat(t.id, e.target.value)}
                      className="w-40"
                    />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  )
}
