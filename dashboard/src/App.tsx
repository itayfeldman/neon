import { useState } from 'react'
import { PriceChart } from './components/PriceChart'
import { OptionsChain } from './components/OptionsChain'
import { GreeksTable } from './components/GreeksTable'

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-slate-900 rounded-xl p-5 border border-slate-800">
      <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400 mb-4">{title}</h2>
      {children}
    </div>
  )
}

export default function App() {
  const [tickerInput, setTickerInput] = useState('AAPL')
  const [expiryInput, setExpiryInput] = useState('')
  const [ticker, setTicker] = useState('AAPL')
  const [expiry, setExpiry] = useState('')

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setTicker(tickerInput.toUpperCase())
    setExpiry(expiryInput)
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      <header className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight mb-4">neon dashboard</h1>
        <form onSubmit={handleSubmit} className="flex gap-3 items-end">
          <label className="flex flex-col gap-1 text-xs text-slate-400">
            Ticker
            <input
              className="bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-sm text-slate-100 w-28 focus:outline-none focus:border-indigo-500"
              value={tickerInput}
              onChange={e => setTickerInput(e.target.value)}
              placeholder="AAPL"
            />
          </label>
          <label className="flex flex-col gap-1 text-xs text-slate-400">
            Expiry (YYYY-MM-DD)
            <input
              className="bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-sm text-slate-100 w-40 focus:outline-none focus:border-indigo-500"
              value={expiryInput}
              onChange={e => setExpiryInput(e.target.value)}
              placeholder="2025-01-17"
            />
          </label>
          <button
            type="submit"
            className="bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium px-4 py-1.5 rounded"
          >
            Load
          </button>
        </form>
      </header>

      <div className="grid gap-5">
        <Panel title={`${ticker} — 1Y Price`}>
          <PriceChart ticker={ticker} />
        </Panel>

        {expiry && (
          <>
            <Panel title={`Options Chain — ${expiry}`}>
              <OptionsChain ticker={ticker} expiry={expiry} />
            </Panel>
            <Panel title={`Greeks — ${expiry}`}>
              <GreeksTable ticker={ticker} expiry={expiry} />
            </Panel>
          </>
        )}
      </div>
    </div>
  )
}
