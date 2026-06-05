import { useState } from 'react'
import { fetchBondPrice, type BondRequest, type BondResponse } from '../api'

const DEFAULTS: BondRequest = {
  face_value: 1000,
  coupon_rate: 0.05,
  coupon_freq: 2,
  issue_date: '20200101',
  maturity_date: '20300101',
  ytm: 0.045,
}

function Stat({ label, value, decimals = 4 }: { label: string; value: number; decimals?: number }) {
  return (
    <div className="flex flex-col bg-slate-800 rounded-lg px-4 py-3">
      <span className="text-xs text-slate-400 uppercase tracking-wider">{label}</span>
      <span className="text-base font-mono text-slate-100 mt-1">{value.toFixed(decimals)}</span>
    </div>
  )
}

function Field({ label, ...props }: React.InputHTMLAttributes<HTMLInputElement> & { label: string }) {
  return (
    <label className="flex flex-col gap-1 text-xs text-slate-400">
      {label}
      <input
        className="bg-slate-800 border border-slate-700 rounded px-2 py-1.5 text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
        {...props}
      />
    </label>
  )
}

export function BondAnalytics() {
  const [form, setForm] = useState<BondRequest>(DEFAULTS)
  const [result, setResult] = useState<BondResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  function set(key: keyof BondRequest, value: string) {
    setForm(f => ({ ...f, [key]: key === 'issue_date' || key === 'maturity_date' ? value : Number(value) }))
  }

  async function handlePrice() {
    setLoading(true)
    setError(null)
    try {
      setResult(await fetchBondPrice(form))
    } catch {
      setError('Failed to price bond.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        <Field label="Face value" type="number" value={form.face_value} onChange={e => set('face_value', e.target.value)} />
        <Field label="Coupon rate (0–1)" type="number" step="0.01" value={form.coupon_rate} onChange={e => set('coupon_rate', e.target.value)} />
        <Field label="Coupon freq / yr" type="number" value={form.coupon_freq} onChange={e => set('coupon_freq', e.target.value)} />
        <Field label="Issue date (YYYYMMDD)" value={form.issue_date} onChange={e => set('issue_date', e.target.value)} />
        <Field label="Maturity date (YYYYMMDD)" value={form.maturity_date} onChange={e => set('maturity_date', e.target.value)} />
        <Field label="YTM (0–1)" type="number" step="0.001" value={form.ytm} onChange={e => set('ytm', e.target.value)} />
      </div>
      <button
        onClick={handlePrice}
        disabled={loading}
        className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm font-medium px-4 py-1.5 rounded"
      >
        {loading ? 'Pricing…' : 'Price'}
      </button>
      {error && <p className="text-red-400 text-sm">{error}</p>}
      {result && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <Stat label="Dirty price" value={result.dirty_price} decimals={2} />
          <Stat label="Clean price" value={result.clean_price} decimals={2} />
          <Stat label="Accrued int." value={result.accrued_interest} decimals={2} />
          <Stat label="Mod. duration" value={result.modified_duration} />
          <Stat label="Mac. duration" value={result.macaulay_duration} />
          <Stat label="DV01" value={result.dv01} />
          <Stat label="Convexity" value={result.convexity} decimals={2} />
        </div>
      )}
    </div>
  )
}
