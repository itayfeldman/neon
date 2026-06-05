import { useQuery } from '@tanstack/react-query'
import {
  ComposedChart, Area, Line, XAxis, YAxis, Tooltip,
  ReferenceLine, ResponsiveContainer,
} from 'recharts'
import { fetchOptions } from '../api'

interface Props { ticker: string; expiry: string; spot: number }

function atmStraddle(calls: { strike: number; bid: number; ask: number }[], puts: { strike: number; bid: number; ask: number }[], spot: number) {
  const nearest = (rows: typeof calls) =>
    rows.reduce((best, r) => Math.abs(r.strike - spot) < Math.abs(best.strike - spot) ? r : best, rows[0])
  const atmCall = nearest(calls)
  const atmPut = nearest(puts)
  const callMid = (atmCall.bid + atmCall.ask) / 2
  const putMid = (atmPut.bid + atmPut.ask) / 2
  return { straddle: callMid + putMid, strike: atmCall.strike }
}

export function ExpectedMoveChart({ ticker, expiry, spot }: Props) {
  const { data, isPending, isError } = useQuery({
    queryKey: ['options', ticker, expiry],
    queryFn: () => fetchOptions(ticker, expiry),
  })

  if (isPending) return <div className="text-slate-400">Loading…</div>
  if (isError) return <div className="text-red-400">Failed to load expected move data.</div>

  const validCalls = data.calls.filter(c => c.bid > 0 || c.ask > 0)
  const validPuts = data.puts.filter(p => p.bid > 0 || p.ask > 0)
  if (!validCalls.length || !validPuts.length) return <div className="text-slate-400">No bid/ask data.</div>

  const { straddle, strike } = atmStraddle(validCalls, validPuts, spot)
  const upper = strike + straddle
  const lower = strike - straddle

  // Build a simple bar across the price range to visualise the expected move band
  const min = spot * 0.75
  const max = spot * 1.25
  const step = (max - min) / 100
  const points = []
  for (let s = min; s <= max; s += step) {
    const inBand = s >= lower && s <= upper
    points.push({ price: +s.toFixed(2), band: inBand ? straddle * 0.15 : 0 })
  }

  const pct = ((straddle / spot) * 100).toFixed(1)

  return (
    <div className="space-y-2">
      <div className="flex gap-6 text-sm flex-wrap">
        <span className="text-slate-400">Straddle: <span className="text-cyan-400 font-mono">${straddle.toFixed(2)}</span></span>
        <span className="text-slate-400">Expected move: <span className="text-cyan-400 font-mono">±${straddle.toFixed(2)} ({pct}%)</span></span>
        <span className="text-slate-400">Range: <span className="text-green-400 font-mono">${lower.toFixed(2)} – ${upper.toFixed(2)}</span></span>
      </div>
      <ResponsiveContainer width="100%" height={200}>
        <ComposedChart data={points}>
          <XAxis dataKey="price" tick={{ fontSize: 10 }} tickLine={false} tickFormatter={v => `$${v}`} />
          <YAxis hide />
          <Tooltip labelFormatter={l => `Price: $${l}`} formatter={() => ''} />
          <Area type="monotone" dataKey="band" fill="#22d3ee" fillOpacity={0.15} stroke="none" />
          <Line type="monotone" dataKey={() => 0} stroke="transparent" dot={false} />
          <ReferenceLine x={spot} stroke="#6366f1" strokeDasharray="4 2" label={{ value: 'spot', fill: '#6366f1', fontSize: 10 }} />
          <ReferenceLine x={upper} stroke="#22d3ee" strokeDasharray="4 2" label={{ value: `+EM $${upper.toFixed(0)}`, fill: '#22d3ee', fontSize: 9 }} />
          <ReferenceLine x={lower} stroke="#22d3ee" strokeDasharray="4 2" label={{ value: `-EM $${lower.toFixed(0)}`, fill: '#22d3ee', fontSize: 9 }} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}
