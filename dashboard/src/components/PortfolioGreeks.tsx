import { useState } from 'react'
import { fetchPortfolioGreeks, type PositionRequest, type PortfolioGreeksResponse } from '../api'

const EXAMPLE = JSON.stringify([
  { ticker: 'AAPL', expiry: '2026-01-16', strike: 200, option_type: 'call', quantity: 10 },
], null, 2)

function GreekStat({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex flex-col items-center bg-slate-800 rounded-lg px-5 py-3">
      <span className="text-xs text-slate-400 uppercase tracking-wider">{label}</span>
      <span className="text-lg font-mono text-slate-100 mt-1">{value.toFixed(4)}</span>
    </div>
  )
}

export function PortfolioGreeks() {
  const [raw, setRaw] = useState(EXAMPLE)
  const [parseError, setParseError] = useState<string | null>(null)
  const [result, setResult] = useState<PortfolioGreeksResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [fetchError, setFetchError] = useState<string | null>(null)

  async function handleCalculate() {
    let positions: PositionRequest[]
    try {
      positions = JSON.parse(raw)
      setParseError(null)
    } catch {
      setParseError('Invalid JSON')
      return
    }

    setLoading(true)
    setFetchError(null)
    try {
      const data = await fetchPortfolioGreeks(positions)
      setResult(data)
    } catch {
      setFetchError('Failed to calculate portfolio Greeks.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <textarea
        className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm font-mono text-slate-100 focus:outline-none focus:border-indigo-500 resize-none"
        rows={6}
        value={raw}
        onChange={e => setRaw(e.target.value)}
      />
      {parseError && <p className="text-red-400 text-sm">{parseError}</p>}
      <button
        onClick={handleCalculate}
        disabled={loading}
        className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm font-medium px-4 py-1.5 rounded"
      >
        {loading ? 'Calculating…' : 'Calculate'}
      </button>
      {fetchError && <p className="text-red-400 text-sm">{fetchError}</p>}
      {result && (
        <div className="flex gap-4 flex-wrap">
          <GreekStat label="Delta" value={result.delta} />
          <GreekStat label="Gamma" value={result.gamma} />
          <GreekStat label="Vega" value={result.vega} />
          <GreekStat label="Theta" value={result.theta} />
        </div>
      )}
    </div>
  )
}
