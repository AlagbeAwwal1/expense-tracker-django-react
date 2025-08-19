import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle,
  AlertDialogTrigger
} from '@/components/ui/alert-dialog'
import React from 'react'

export default function HeaderBar({ month, setMonth, onApply, onClear }) {
  return (
    <div className="flex items-center justify-between">
      <h2 className="text-2xl font-semibold">💸 Expense Tracker</h2>
      <div className="flex gap-2">
        <Input placeholder="YYYY-MM" value={month} onChange={(e)=>setMonth(e.target.value)} className="w-32" />
        <Button variant="secondary" onClick={onApply}>Apply</Button>

        <AlertDialog>
          <AlertDialogTrigger asChild>
            <Button variant="destructive">Clear All</Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Clear all transactions?</AlertDialogTitle>
              <AlertDialogDescription>
                This will permanently delete every transaction in the database. This action cannot be undone.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction onClick={onClear}>Yes, clear</AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </div>
  )
}
