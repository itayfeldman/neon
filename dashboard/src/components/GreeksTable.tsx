import { useQuery } from '@tanstack/react-query'
import { fetchGreeks } from '../api'

interface Props {
  ticker: string
  expiry: string
}

export function GreeksTable({ ticker, expiry }: Props) {
  const { data, isPending, isError } = useQuery({
    queryKey: ['greeks', ticker, expiry],
    queryFn: () => fetchGreeks(ticker, expiry),
  })

  if (isPending) return <div className="text-slate-400">Loading…</div>
  if (isError) return <div className="text-red-400">Failed to load Greeks.</div>

  return (
    <div className="overflow-auto max-h-80">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-slate-500 border-b border-slate-700">
            <th className="pb-1 pr-4">Strike</th>
            <th className="pb-1 pr-4">Type</th>
            <th className="pb-1 pr-4">Delta</th>
            <th className="pb-1 pr-4">Gamma</th>
            <th className="pb-1 pr-4">Vega</th>
            <th className="pb-1">Theta</th>
          </tr>
        </thead>
        <tbody>
          {data.rows.map((r) => (
            <tr key={`${r.strike}-${r.option_type}`} className="border-b border-slate-800 hover:bg-slate-800/50">
              <td className="py-1 pr-4">{r.strike.toFixed(1)}</td>
              <td className="py-1 pr-4 capitalize">{r.option_type}</td>
              <td className="py-1 pr-4">{r.delta.toFixed(3)}</td>
              <td className="py-1 pr-4">{r.gamma.toFixed(4)}</td>
              <td className="py-1 pr-4">{r.vega.toFixed(3)}</td>
              <td className="py-1">{r.theta.toFixed(3)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
