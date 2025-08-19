import React, { useEffect, useMemo, useState } from 'react'
import HeaderBar from '@/components/HeaderBar'
import UploadCard from '@/components/UploadCard'
import DonutCard from '@/components/DonutCard'
import MonthlyBarCard from '@/components/MonthlyBarCard'
import TransactionsTable from '@/components/TransactionsTable'
import {
  fetchTransactions, fetchSpendByCategory, fetchMonthlyCategoryTotals,
  uploadCSV, patchTransactionCategory, clearTransactions
} from '@/lib/api'

export default function App() {
  const [fileRes, setFileRes] = useState(null)
  const [month, setMonth] = useState('')           // YYYY-MM
  const [txs, setTxs] = useState([])
  const [analytic, setAnalytic] = useState([])
  const [monthly, setMonthly] = useState([])
  const [err, setErr] = useState('')

  const loadTx = async () => {
    setErr('')
    try { setTxs(await fetchTransactions(month)) }
    catch (e) { setErr(e.message || 'Failed to load transactions') }
  }
  const loadAnalytic = async () => {
    setErr('')
    try { setAnalytic(await fetchSpendByCategory(month)) }
    catch (e) { setErr(e.message || 'Failed to load analytics') }
  }
  const loadMonthly = async () => {
    setErr('')
    try { setMonthly(await fetchMonthlyCategoryTotals()) }
    catch (e) { setErr(e.message || 'Failed to load monthly totals') }
  }

  const onUpload = async (file) => {
    setErr('')
    try {
      const data = await uploadCSV(file)
      setFileRes(data)
      await Promise.all([loadTx(), loadAnalytic(), loadMonthly()])
    } catch (e) { setErr(e.message || 'Upload failed') }
  }

  const onUpdateCat = async (id, category) => {
    setErr('')
    try {
      await patchTransactionCategory(id, category)
      await loadTx()
      await loadAnalytic()
      await loadMonthly()
    } catch (e) { setErr(e.message || 'Failed to update category') }
  }

  const onApply = async () => {
    await Promise.all([loadTx(), loadAnalytic()])
  }

  const onClear = async () => {
    setErr('')
    try {
      await clearTransactions()
      setTxs([])
      setAnalytic([])
      await loadMonthly()
    } catch (e) { setErr(e.message || 'Failed to clear transactions') }
  }

  useEffect(() => { loadTx(); loadAnalytic(); loadMonthly() }, [])

  const categoryKeys = useMemo(() => {
    const keys = new Set()
    monthly.forEach(row => Object.keys(row).forEach(k => { if (k !== 'month') keys.add(k) }))
    return Array.from(keys)
  }, [monthly])

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <div className="mx-auto max-w-6xl p-6 space-y-6">
        <HeaderBar month={month} setMonth={setMonth} onApply={onApply} onClear={onClear} />
        {err && <div className="text-red-600">{err}</div>}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <UploadCard onUpload={onUpload} fileRes={fileRes} />
          <DonutCard data={analytic} />
        </div>

        <MonthlyBarCard data={monthly} categoryKeys={categoryKeys} />
        <TransactionsTable txs={txs} onUpdateCat={onUpdateCat} />
      </div>
    </div>
  )
}
