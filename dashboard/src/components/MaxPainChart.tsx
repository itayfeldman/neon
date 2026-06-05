import { useQuery } from '@tanstack/react-query'
import { LineChart, Line, XAxis, YAxis, Tooltip, ReferenceLine, ResponsiveContainer } from 'recharts'
import { fetchOptions } from '../api'

interface Props { ticker: string; expiry: string; spot: number }

function computeMaxPain(calls: { strike: number; open_interest: number }[], puts: { strike: number; open_interest: number }[]) {
  const strikes = [...new Set([...calls.map(c => c.strike), ...puts.map(p => p.strike)])].sort((a, b) => a - b)
  const callMap = new Map(calls.map(c => [c.strike, c.open_interest]))
  const putMap = new Map(puts.map(p => [p.strike, p.open_interest]))

  const points = strikes.map(pin => {
    // Pain = sum over all strikes of (OI × intrinsic value at expiry price = pin)
    const callPain = strikes.reduce((sum, k) => sum + (callMap.get(k) ?? 0) * Math.max(pin - k, 0), 0)
    const putPain = strikes.reduce((sum, k) => sum + (putMap.get(k) ?? 0) * Math.max(k - pin, 0), 0)
    return { strike: pin, pain: callPain + putPain }
  })

  const maxPainStrike = points.reduce((min, p) => p.pain < min.pain ? p : min, points[0]).strike
  return { points, maxPainStrike }
}

export function MaxPainChart({ ticker, expiry, spot }: Props) {
  const { data, isPending, isError } = useQuery({
    queryKey: ['options', ticker, expiry],
    queryFn: () => fetchOptions(ticker, expiry),
  })

  if (isPending) return <div className="text-slate-400">Loading…</div>
  if (isError) return <div className="text-red-400">Failed to load max pain data.</div>

  const { points, maxPainStrike } = computeMaxPain(data.calls, data.puts)

  return (
    <div className="space-y-2">
      <div className="flex gap-6 text-sm">
        <span className="text-slate-400">Max Pain: <span className="text-amber-400 font-mono">${maxPainStrike}</span></span>
        <span className="text-slate-400">Spot: <span className="text-indigo-400 font-mono">${spot.toFixed(2)}</span></span>
      </div>
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={points}>
          <XAxis dataKey="strike" tick={{ fontSize: 10 }} tickLine={false} />
          <YAxis tick={{ fontSize: 10 }} tickLine={false} axisLine={false} tickFormatter={v => `$${(v / 1e6).toFixed(1)}M`} />
          <Tooltip formatter={(v) => typeof v === 'number' ? `$${(v / 1e6).toFixed(2)}M` : v} labelFormatter={l => `Strike: $${l}`} />
          <ReferenceLine x={maxPainStrike} stroke="#f59e0b" strokeDasharray="4 2" label={{ value: 'max pain', fill: '#f59e0b', fontSize: 10 }} />
          <ReferenceLine x={spot} stroke="#6366f1" strokeDasharray="4 2" label={{ value: 'spot', fill: '#6366f1', fontSize: 10 }} />
          <Line type="monotone" dataKey="pain" dot={false} stroke="#22d3ee" strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
