import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import React from 'react'

export default function UploadCard({ onUpload, fileRes }) {
  const handleChange = (e) => {
    const f = e.target.files?.[0]
    if (f) onUpload(f)
  }
  return (
    <Card>
      <CardHeader>
        <CardTitle>Upload CSV</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <Input type="file" onChange={handleChange} />
        <pre className="text-xs text-slate-600 max-h-28 overflow-auto bg-slate-100 p-2 rounded">
          {fileRes ? JSON.stringify(fileRes, null, 2) : ''}
        </pre>
      </CardContent>
    </Card>
  )
}
