import { useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { fetchHistory } from '../api'

interface Props {
  ticker: string
  onSpot?: (spot: number) => void
}

export function PriceChart({ ticker, onSpot }: Props) {
  const { data, isPending, isError } = useQuery({
    queryKey: ['history', ticker],
    queryFn: () => fetchHistory(ticker),
  })

  if (isPending) return <div className="text-slate-400">Loading…</div>
  if (isError) return <div className="text-red-400">Failed to load price history.</div>

  const latestClose = data.closes[data.closes.length - 1]
  useEffect(() => {
    if (onSpot && latestClose) onSpot(latestClose)
  }, [latestClose, onSpot])

  const points = data.dates.map((date, i) => ({ date, close: data.closes[i] }))

  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={points}>
        <XAxis dataKey="date" tick={{ fontSize: 11 }} tickLine={false} interval="preserveStartEnd" />
        <YAxis domain={['auto', 'auto']} tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
        <Tooltip formatter={(v) => typeof v === 'number' ? `$${v.toFixed(2)}` : v} />
        <Line type="monotone" dataKey="close" dot={false} stroke="#6366f1" strokeWidth={2} />
      </LineChart>
    </ResponsiveContainer>
  )
}
