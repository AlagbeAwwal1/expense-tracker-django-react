import React, { useEffect, useState } from 'react'
import { PieChart, Pie, Tooltip, Cell, ResponsiveContainer } from 'recharts'

const API = 'http://127.0.0.1:8000/api'

// ---- tiny fetch helpers ----
async function httpGetJSON(url) {
  const res = await fetch(url)
  if (!res.ok) throw new Error((await res.text()) || res.statusText)
  return res.json()
}

async function httpPatchJSON(url, body) {
  const res = await fetch(url, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error((await res.text()) || res.statusText)
  return res.json()
}

async function httpPostForm(url, formData) {
  const res = await fetch(url, { method: 'POST', body: formData })
  if (!res.ok) throw new Error((await res.text()) || res.statusText)
  return res.json()
}
// ----------------------------

export default function App() {
  const [fileRes, setFileRes] = useState(null)
  const [month, setMonth] = useState('')
  const [txs, setTxs] = useState([])
  const [analytic, setAnalytic] = useState([])
  const [err, setErr] = useState('')

  const upload = async (e) => {
    setErr('')
    const f = e.target.files?.[0]
    if (!f) return
    const fd = new FormData()
    fd.append('file', f)
    try {
      const data = await httpPostForm(`${API}/files/`, fd)
      setFileRes(data)
    } catch (e) {
      setErr(e.message || 'Upload failed')
    }
  }

  const loadTx = async () => {
    setErr('')
    const params = month ? `?month=${encodeURIComponent(month)}` : ''
    try {
      const data = await httpGetJSON(`${API}/transactions/${params}`)
      setTxs(data)
    } catch (e) {
      setErr(e.message || 'Failed to load transactions')
    }
  }

  const updateCat = async (id, category) => {
    setErr('')
    try {
      await httpPatchJSON(`${API}/transactions/${id}/`, { category })
      await loadTx()
    } catch (e) {
      setErr(e.message || 'Failed to update category')
    }
  }

  const loadAnalytic = async () => {
    setErr('')
    const params = month ? `?month=${encodeURIComponent(month)}` : ''
    try {
      const data = await httpGetJSON(`${API}/analytics/spend-by-category/${params}`)
      setAnalytic(data)
    } catch (e) {
      setErr(e.message || 'Failed to load analytics')
    }
  }

  useEffect(() => {
    loadTx()
    loadAnalytic()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div style={{ fontFamily: 'system-ui, Arial', padding: 20, maxWidth: 1100, margin: '0 auto' }}>
      <h2>💸 Expense Tracker</h2>
      <p style={{ color: '#666' }}>Upload CSV, auto-categorize, edit categories, and view spend by category.</p>
      {err && <p style={{ color: 'crimson', marginTop: 8 }}>{err}</p>}

      <section style={{ display: 'flex', gap: 20, flexWrap: 'wrap' }}>
        <div style={{ border: '1px solid #ddd', borderRadius: 8, padding: 12, flex: 1, minWidth: 300 }}>
          <h3>1) Upload CSV</h3>
          <input type="file" onChange={upload} />
          <pre style={{ fontSize: 12, color: '#666' }}>{fileRes ? JSON.stringify(fileRes, null, 2) : ''}</pre>
        </div>
        <div style={{ border: '1px solid #ddd', borderRadius: 8, padding: 12, flex: 1, minWidth: 300 }}>
          <h3>2) Analytics</h3>
          <input placeholder="YYYY-MM" value={month} onChange={(e) => setMonth(e.target.value)} />
          <button onClick={loadAnalytic} style={{ marginLeft: 8 }}>Load</button>
          <div style={{ height: 240 }}>
            <ResponsiveContainer>
              <PieChart>
                <Pie dataKey="amount" data={analytic} nameKey="category" outerRadius={80} label>
                  {analytic.map((_, i) => <Cell key={i} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <ul>
            {analytic.map(x => <li key={x.category}>{x.category}: ${x.amount.toFixed(2)}</li>)}
          </ul>
        </div>
      </section>

      <section style={{ marginTop: 16 }}>
        <h3>3) Transactions</h3>
        <input placeholder="YYYY-MM" value={month} onChange={(e) => setMonth(e.target.value)} />
        <button onClick={loadTx} style={{ marginLeft: 8 }}>Refresh</button>
        <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: 8 }}>
          <thead>
            <tr>
              <th style={th}>Date</th>
              <th style={th}>Merchant</th>
              <th style={th}>Description</th>
              <th style={th}>Amount</th>
              <th style={th}>Type</th>
              <th style={th}>Category</th>
            </tr>
          </thead>
          <tbody>
            {txs.map(t => (
              <tr key={t.id}>
                <td style={td}>{t.date}</td>
                <td style={td}>{t.merchant}</td>
                <td style={td}>{t.description}</td>
                <td style={td}>${Number(t.amount).toFixed(2)}</td>
                <td style={td}>{t.type}</td>
                <td style={td}>
                  <input defaultValue={t.category} onBlur={(e) => updateCat(t.id, e.target.value)} size="12" />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  )
}

const th = { border: '1px solid #ddd', padding: '6px', textAlign: 'left', background: '#fafafa' }
const td = { border: '1px solid #eee', padding: '6px' }
