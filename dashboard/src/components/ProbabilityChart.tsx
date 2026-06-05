import { useQuery } from '@tanstack/react-query'
import { LineChart, Line, XAxis, YAxis, Tooltip, Legend, ReferenceLine, ResponsiveContainer } from 'recharts'
import { fetchOptions } from '../api'

interface Props { ticker: string; expiry: string; spot: number }

function normalPdf(x: number, mu: number, sigma: number) {
  const z = (x - mu) / sigma
  return Math.exp(-0.5 * z * z) / (sigma * Math.sqrt(2 * Math.PI))
}

function buildDistributions(spot: number, calls: { strike: number; iv: number }[]) {
  const atm = calls.reduce((best, c) => Math.abs(c.strike - spot) < Math.abs(best.strike - spot) ? c : best, calls[0])
  const iv = atm?.iv ?? 0.3

  const min = spot * 0.6
  const max = spot * 1.4
  const step = (max - min) / 200

  const points = []
  for (let s = min; s <= max; s += step) {
    // Lognormal: log-return normally distributed with σ=iv
    const logMu = Math.log(spot)
    const logSig = iv
    const lognormal = normalPdf(Math.log(s), logMu - 0.5 * logSig * logSig, logSig) / s

    // Market-implied: interpolate iv by strike → local vol approximation
    const nearCall = calls.reduce((best, c) => Math.abs(c.strike - s) < Math.abs(best.strike - s) ? c : best, calls[0])
    const localIv = nearCall?.iv ?? iv
    const implied = normalPdf(Math.log(s), logMu - 0.5 * localIv * localIv, localIv) / s

    points.push({ price: +s.toFixed(2), lognormal: +lognormal.toFixed(6), implied: +implied.toFixed(6) })
  }
  return points
}

export function ProbabilityChart({ ticker, expiry, spot }: Props) {
  const { data, isPending, isError } = useQuery({
    queryKey: ['options', ticker, expiry],
    queryFn: () => fetchOptions(ticker, expiry),
  })

  if (isPending) return <div className="text-slate-400">Loading…</div>
  if (isError) return <div className="text-red-400">Failed to load probability data.</div>

  const validCalls = data.calls.filter(c => c.iv > 0.01)
  if (validCalls.length === 0) return <div className="text-slate-400">No IV data available.</div>

  const points = buildDistributions(spot, validCalls)

  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={points}>
        <XAxis dataKey="price" tick={{ fontSize: 10 }} tickLine={false} tickFormatter={v => `$${v}`} />
        <YAxis tick={{ fontSize: 10 }} tickLine={false} axisLine={false} tickFormatter={() => ''} />
        <Tooltip
          labelFormatter={l => `Price: $${l}`}
          formatter={(v, name) => [typeof v === 'number' ? v.toFixed(5) : v, name === 'lognormal' ? 'Lognormal (BS)' : 'Market-implied']}
        />
        <Legend wrapperStyle={{ fontSize: 11 }} />
        <ReferenceLine x={spot} stroke="#6366f1" strokeDasharray="4 2" />
        <Line type="monotone" dataKey="lognormal" dot={false} stroke="#94a3b8" strokeWidth={1.5} strokeDasharray="4 2" name="lognormal" />
        <Line type="monotone" dataKey="implied" dot={false} stroke="#22d3ee" strokeWidth={2} name="implied" />
      </LineChart>
    </ResponsiveContainer>
  )
}
