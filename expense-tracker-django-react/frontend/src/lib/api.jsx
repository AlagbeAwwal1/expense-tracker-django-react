const API = import.meta.env.VITE_API_BASE ?? 'http://127.0.0.1:8000/api'

// ---- tiny fetch core ----
async function httpGetJSON(url) {
  const res = await fetch(url)
  if (!res.ok) throw new Error((await res.text()) || res.statusText)
  return res.json()
}
async function httpPatchJSON(url, body) {
  const res = await fetch(url, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
  if (!res.ok) throw new Error((await res.text()) || res.statusText)
  return res.json()
}
async function httpPostForm(url, formData) {
  const res = await fetch(url, { method: 'POST', body: formData })
  if (!res.ok) throw new Error((await res.text()) || res.statusText)
  return res.json()
}
async function httpDelete(url) {
  const res = await fetch(url, { method: 'DELETE' })
  if (!res.ok) throw new Error((await res.text()) || res.statusText)
  return res.json()
}

// ---- exported API helpers ----
export function fetchTransactions(month) {
  const q = month ? `?month=${encodeURIComponent(month)}` : ''
  return httpGetJSON(`${API}/transactions/${q}`)
}
export function fetchSpendByCategory(month) {
  const q = month ? `?month=${encodeURIComponent(month)}` : ''
  return httpGetJSON(`${API}/analytics/spend-by-category/${q}`)
}
export function fetchMonthlyCategoryTotals() {
  return httpGetJSON(`${API}/analytics/monthly-category-totals/`)
}
export function uploadCSV(file) {
  const fd = new FormData()
  fd.append('file', file)
  return httpPostForm(`${API}/files/`, fd)
}
export function patchTransactionCategory(id, category) {
  return httpPatchJSON(`${API}/transactions/${id}/`, { category })
}
export function clearTransactions() {
  return httpDelete(`${API}/transactions/clear/`)
}
