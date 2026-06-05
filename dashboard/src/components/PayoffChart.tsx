import { useState } from 'react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ReferenceLine, ResponsiveContainer } from 'recharts'

type OptionType = 'call' | 'put'
type Direction = 'long' | 'short'

interface Leg {
  id: number
  type: OptionType
  direction: Direction
  strike: number
  premium: number
  quantity: number
}

function payoff(leg: Leg, spot: number): number {
  const intrinsic = leg.type === 'call'
    ? Math.max(spot - leg.strike, 0)
    : Math.max(leg.strike - spot, 0)
  const sign = leg.direction === 'long' ? 1 : -1
  return sign * leg.quantity * (intrinsic - leg.premium)
}

function buildSeries(legs: Leg[], spot: number) {
  const strikes = legs.map(l => l.strike)
  const min = Math.max(1, Math.min(...strikes) * 0.6)
  const max = Math.max(...strikes) * 1.4
  const step = (max - min) / 200
  const points = []
  for (let s = min; s <= max; s += step) {
    const pnl = legs.reduce((sum, leg) => sum + payoff(leg, s), 0)
    points.push({ spot: +s.toFixed(2), pnl: +pnl.toFixed(2) })
  }
  // always include current spot
  const spotPnl = legs.reduce((sum, leg) => sum + payoff(leg, spot), 0)
  points.push({ spot, pnl: +spotPnl.toFixed(2) })
  return points.sort((a, b) => a.spot - b.spot)
}

const PRESETS: { label: string; legs: Omit<Leg, 'id'>[] }[] = [
  { label: 'Long call', legs: [{ type: 'call', direction: 'long', strike: 100, premium: 5, quantity: 1 }] },
  { label: 'Long put', legs: [{ type: 'put', direction: 'long', strike: 100, premium: 5, quantity: 1 }] },
  { label: 'Bull call spread', legs: [
    { type: 'call', direction: 'long', strike: 95, premium: 7, quantity: 1 },
    { type: 'call', direction: 'short', strike: 105, premium: 3, quantity: 1 },
  ]},
  { label: 'Bear put spread', legs: [
    { type: 'put', direction: 'long', strike: 105, premium: 7, quantity: 1 },
    { type: 'put', direction: 'short', strike: 95, premium: 3, quantity: 1 },
  ]},
  { label: 'Long straddle', legs: [
    { type: 'call', direction: 'long', strike: 100, premium: 5, quantity: 1 },
    { type: 'put', direction: 'long', strike: 100, premium: 5, quantity: 1 },
  ]},
  { label: 'Short strangle', legs: [
    { type: 'call', direction: 'short', strike: 110, premium: 3, quantity: 1 },
    { type: 'put', direction: 'short', strike: 90, premium: 3, quantity: 1 },
  ]},
  { label: 'Iron condor', legs: [
    { type: 'put', direction: 'long', strike: 80, premium: 1, quantity: 1 },
    { type: 'put', direction: 'short', strike: 90, premium: 3, quantity: 1 },
    { type: 'call', direction: 'short', strike: 110, premium: 3, quantity: 1 },
    { type: 'call', direction: 'long', strike: 120, premium: 1, quantity: 1 },
  ]},
]

let nextId = 1

export function PayoffChart({ spot = 100 }: { spot?: number }) {
  const [legs, setLegs] = useState<Leg[]>([
    { id: nextId++, type: 'call', direction: 'long', strike: spot, premium: 5, quantity: 1 },
  ])

  function addLeg() {
    setLegs(prev => [...prev, { id: nextId++, type: 'call', direction: 'long', strike: spot, premium: 5, quantity: 1 }])
  }

  function removeLeg(id: number) {
    setLegs(prev => prev.filter(l => l.id !== id))
  }

  function updateLeg(id: number, patch: Partial<Leg>) {
    setLegs(prev => prev.map(l => l.id === id ? { ...l, ...patch } : l))
  }

  function applyPreset(preset: typeof PRESETS[number]) {
    setLegs(preset.legs.map(l => ({ ...l, id: nextId++, strike: l.strike })))
  }

  const series = legs.length > 0 ? buildSeries(legs, spot) : []
  const maxAbs = Math.max(...series.map(p => Math.abs(p.pnl)), 1)

  return (
    <div className="space-y-4">
      {/* Presets */}
      <div className="flex flex-wrap gap-2">
        {PRESETS.map(p => (
          <button
            key={p.label}
            onClick={() => applyPreset(p)}
            className="text-xs bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded px-3 py-1 text-slate-300"
          >
            {p.label}
          </button>
        ))}
      </div>

      {/* Leg builder */}
      <div className="space-y-2">
        {legs.map(leg => (
          <div key={leg.id} className="flex flex-wrap gap-2 items-center text-sm">
            <select
              value={leg.direction}
              onChange={e => updateLeg(leg.id, { direction: e.target.value as Direction })}
              className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-slate-100 text-xs"
            >
              <option value="long">Long</option>
              <option value="short">Short</option>
            </select>
            <select
              value={leg.type}
              onChange={e => updateLeg(leg.id, { type: e.target.value as OptionType })}
              className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-slate-100 text-xs"
            >
              <option value="call">Call</option>
              <option value="put">Put</option>
            </select>
            <label className="flex items-center gap-1 text-xs text-slate-400">
              Strike
              <input
                type="number"
                value={leg.strike}
                onChange={e => updateLeg(leg.id, { strike: +e.target.value })}
                className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-slate-100 w-20"
              />
            </label>
            <label className="flex items-center gap-1 text-xs text-slate-400">
              Premium
              <input
                type="number"
                value={leg.premium}
                step="0.5"
                onChange={e => updateLeg(leg.id, { premium: +e.target.value })}
                className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-slate-100 w-20"
              />
            </label>
            <label className="flex items-center gap-1 text-xs text-slate-400">
              Qty
              <input
                type="number"
                value={leg.quantity}
                min="1"
                onChange={e => updateLeg(leg.id, { quantity: +e.target.value })}
                className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-slate-100 w-16"
              />
            </label>
            <button
              onClick={() => removeLeg(leg.id)}
              className="text-slate-500 hover:text-red-400 text-xs px-1"
            >
              ✕
            </button>
          </div>
        ))}
        <button
          onClick={addLeg}
          className="text-xs text-indigo-400 hover:text-indigo-300"
        >
          + Add leg
        </button>
      </div>

      {/* Chart */}
      {series.length > 0 && (
        <ResponsiveContainer width="100%" height={260}>
          <LineChart data={series}>
            <XAxis dataKey="spot" tick={{ fontSize: 10 }} tickLine={false} label={{ value: 'Underlying price', position: 'insideBottom', offset: -2, fontSize: 10, fill: '#94a3b8' }} />
            <YAxis domain={[-maxAbs * 1.1, maxAbs * 1.1]} tick={{ fontSize: 10 }} tickLine={false} axisLine={false} label={{ value: 'P&L', angle: -90, position: 'insideLeft', fontSize: 10, fill: '#94a3b8' }} />
            <Tooltip formatter={(v) => typeof v === 'number' ? v.toFixed(2) : v} labelFormatter={(l) => `Spot: ${l}`} />
            <ReferenceLine y={0} stroke="#475569" strokeDasharray="4 2" />
            <ReferenceLine x={spot} stroke="#6366f1" strokeDasharray="4 2" />
            <Line type="monotone" dataKey="pnl" dot={false} stroke="#22d3ee" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}
