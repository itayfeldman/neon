import { useQuery } from '@tanstack/react-query'
import { LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { fetchOptions, fetchGreeks } from '../api'

interface SmileChartProps {
  title: string
  xLabel: string
  yLabel: string
  data: { x: number; calls: number; puts: number }[]
}

function SmileChart({ title, xLabel, yLabel, data }: SmileChartProps) {
  return (
    <div>
      <p className="text-xs text-slate-400 mb-2">{title}</p>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={data}>
          <XAxis dataKey="x" tick={{ fontSize: 10 }} tickLine={false} label={{ value: xLabel, position: 'insideBottom', offset: -2, fontSize: 10, fill: '#94a3b8' }} />
          <YAxis tick={{ fontSize: 10 }} tickLine={false} axisLine={false} label={{ value: yLabel, angle: -90, position: 'insideLeft', fontSize: 10, fill: '#94a3b8' }} />
          <Tooltip formatter={(v) => typeof v === 'number' ? v.toFixed(4) : v} />
          <Legend wrapperStyle={{ fontSize: 11 }} />
          <Line type="monotone" dataKey="calls" dot={false} stroke="#6366f1" strokeWidth={2} />
          <Line type="monotone" dataKey="puts" dot={false} stroke="#f43f5e" strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

interface Props {
  ticker: string
  expiry: string
}

export function IVSmile({ ticker, expiry }: Props) {
  const { data, isPending, isError } = useQuery({
    queryKey: ['options', ticker, expiry],
    queryFn: () => fetchOptions(ticker, expiry),
  })

  if (isPending) return <div className="text-slate-400 text-sm">Loading…</div>
  if (isError) return <div className="text-red-400 text-sm">Failed to load IV smile.</div>

  const callMap = new Map(data.calls.map(r => [r.strike, r.iv * 100]))
  const putMap = new Map(data.puts.map(r => [r.strike, r.iv * 100]))
  const strikes = [...new Set([...callMap.keys(), ...putMap.keys()])].sort((a, b) => a - b)
  const points = strikes.map(x => ({ x, calls: callMap.get(x) ?? NaN, puts: putMap.get(x) ?? NaN }))

  return <SmileChart title="IV Smile" xLabel="Strike" yLabel="IV %" data={points} />
}

export function DeltaSmile({ ticker, expiry }: Props) {
  const { data, isPending, isError } = useQuery({
    queryKey: ['greeks', ticker, expiry],
    queryFn: () => fetchGreeks(ticker, expiry),
  })

  if (isPending) return <div className="text-slate-400 text-sm">Loading…</div>
  if (isError) return <div className="text-red-400 text-sm">Failed to load Greeks.</div>

  const calls = data.rows.filter(r => r.option_type === 'call').sort((a, b) => a.strike - b.strike)
  const puts = data.rows.filter(r => r.option_type === 'put').sort((a, b) => a.strike - b.strike)
  const strikes = [...new Set([...calls.map(r => r.strike), ...puts.map(r => r.strike)])].sort((a, b) => a - b)
  const callMap = new Map(calls.map(r => [r.strike, r.delta]))
  const putMap = new Map(puts.map(r => [r.strike, r.delta]))
  const points = strikes.map(x => ({ x, calls: callMap.get(x) ?? NaN, puts: putMap.get(x) ?? NaN }))

  return <SmileChart title="Delta vs Strike" xLabel="Strike" yLabel="Δ" data={points} />
}

export function GammaSmile({ ticker, expiry }: Props) {
  const { data, isPending, isError } = useQuery({
    queryKey: ['greeks', ticker, expiry],
    queryFn: () => fetchGreeks(ticker, expiry),
  })

  if (isPending) return <div className="text-slate-400 text-sm">Loading…</div>
  if (isError) return <div className="text-red-400 text-sm">Failed to load Greeks.</div>

  const calls = data.rows.filter(r => r.option_type === 'call').sort((a, b) => a.strike - b.strike)
  const puts = data.rows.filter(r => r.option_type === 'put').sort((a, b) => a.strike - b.strike)
  const strikes = [...new Set([...calls.map(r => r.strike), ...puts.map(r => r.strike)])].sort((a, b) => a - b)
  const callMap = new Map(calls.map(r => [r.strike, r.gamma]))
  const putMap = new Map(puts.map(r => [r.strike, r.gamma]))
  const points = strikes.map(x => ({ x, calls: callMap.get(x) ?? NaN, puts: putMap.get(x) ?? NaN }))

  return <SmileChart title="Gamma vs Strike" xLabel="Strike" yLabel="Γ" data={points} />
}

export function ThetaSmile({ ticker, expiry }: Props) {
  const { data, isPending, isError } = useQuery({
    queryKey: ['greeks', ticker, expiry],
    queryFn: () => fetchGreeks(ticker, expiry),
  })

  if (isPending) return <div className="text-slate-400 text-sm">Loading…</div>
  if (isError) return <div className="text-red-400 text-sm">Failed to load Greeks.</div>

  const calls = data.rows.filter(r => r.option_type === 'call').sort((a, b) => a.strike - b.strike)
  const puts = data.rows.filter(r => r.option_type === 'put').sort((a, b) => a.strike - b.strike)
  const strikes = [...new Set([...calls.map(r => r.strike), ...puts.map(r => r.strike)])].sort((a, b) => a - b)
  const callMap = new Map(calls.map(r => [r.strike, r.theta]))
  const putMap = new Map(puts.map(r => [r.strike, r.theta]))
  const points = strikes.map(x => ({ x, calls: callMap.get(x) ?? NaN, puts: putMap.get(x) ?? NaN }))

  return <SmileChart title="Theta vs Strike" xLabel="Strike" yLabel="Θ" data={points} />
}
