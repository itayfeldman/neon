import { useQuery } from '@tanstack/react-query'
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ReferenceLine, ResponsiveContainer } from 'recharts'
import { fetchOptions } from '../api'

interface Props { ticker: string; expiry: string; spot: number }

export function OpenInterestChart({ ticker, expiry, spot }: Props) {
  const { data, isPending, isError } = useQuery({
    queryKey: ['options', ticker, expiry],
    queryFn: () => fetchOptions(ticker, expiry),
  })

  if (isPending) return <div className="text-slate-400">Loading…</div>
  if (isError) return <div className="text-red-400">Failed to load open interest.</div>

  const callMap = new Map(data.calls.map(r => [r.strike, r.open_interest]))
  const putMap = new Map(data.puts.map(r => [r.strike, r.open_interest]))
  const strikes = [...new Set([...callMap.keys(), ...putMap.keys()])].sort((a, b) => a - b)
  const points = strikes.map(s => ({ strike: s, calls: callMap.get(s) ?? 0, puts: putMap.get(s) ?? 0 }))

  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={points} barCategoryGap="20%">
        <XAxis dataKey="strike" tick={{ fontSize: 10 }} tickLine={false} />
        <YAxis tick={{ fontSize: 10 }} tickLine={false} axisLine={false} />
        <Tooltip formatter={(v) => typeof v === 'number' ? v.toLocaleString() : v} />
        <Legend wrapperStyle={{ fontSize: 11 }} />
        <ReferenceLine x={spot} stroke="#6366f1" strokeDasharray="4 2" label={{ value: 'spot', fill: '#6366f1', fontSize: 10 }} />
        <Bar dataKey="calls" fill="#6366f1" opacity={0.8} />
        <Bar dataKey="puts" fill="#f43f5e" opacity={0.8} />
      </BarChart>
    </ResponsiveContainer>
  )
}
