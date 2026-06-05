import { useQuery } from '@tanstack/react-query'
import { fetchOptions, type OptionRow } from '../api'

interface Props {
  ticker: string
  expiry: string
}

function OptionTable({ rows, label }: { rows: OptionRow[]; label: string }) {
  return (
    <div>
      <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">{label}</h3>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-slate-500 border-b border-slate-700">
            <th className="pb-1 pr-4">Strike</th>
            <th className="pb-1 pr-4">IV</th>
            <th className="pb-1 pr-4">Bid</th>
            <th className="pb-1 pr-4">Ask</th>
            <th className="pb-1">Vol</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.strike} className="border-b border-slate-800 hover:bg-slate-800/50">
              <td className="py-1 pr-4">{r.strike.toFixed(1)}</td>
              <td className="py-1 pr-4">{(r.iv * 100).toFixed(1)}%</td>
              <td className="py-1 pr-4">{r.bid.toFixed(2)}</td>
              <td className="py-1 pr-4">{r.ask.toFixed(2)}</td>
              <td className="py-1">{r.volume.toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function OptionsChain({ ticker, expiry }: Props) {
  const { data, isPending, isError } = useQuery({
    queryKey: ['options', ticker, expiry],
    queryFn: () => fetchOptions(ticker, expiry),
  })

  if (isPending) return <div className="text-slate-400">Loading…</div>
  if (isError) return <div className="text-red-400">Failed to load options chain.</div>

  return (
    <div className="grid grid-cols-2 gap-6 overflow-auto max-h-80">
      <OptionTable rows={data.calls} label="Calls" />
      <OptionTable rows={data.puts} label="Puts" />
    </div>
  )
}
