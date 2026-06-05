import { useState } from 'react'
import { PriceChart } from './components/PriceChart'
import { OptionsChain } from './components/OptionsChain'
import { GreeksTable } from './components/GreeksTable'
import { VolSurface } from './components/VolSurface'
import { IVSmile, DeltaSmile, GammaSmile, ThetaSmile } from './components/SmileChart'
import { PortfolioGreeks } from './components/PortfolioGreeks'
import { BondAnalytics } from './components/BondAnalytics'
import { PayoffChart } from './components/PayoffChart'

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-slate-900 rounded-xl p-5 border border-slate-800">
      <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-4">{title}</h2>
      {children}
    </div>
  )
}

type Tab = 'analytics' | 'payoff'

export default function App() {
  const [tickerInput, setTickerInput] = useState('AAPL')
  const [expiryInput, setExpiryInput] = useState('')
  const [ticker, setTicker] = useState('AAPL')
  const [expiry, setExpiry] = useState('')
  const [tab, setTab] = useState<Tab>('analytics')
  const [spot, setSpot] = useState(100)

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setTicker(tickerInput.toUpperCase())
    setExpiry(expiryInput)
  }

  const tabClass = (t: Tab) =>
    `px-4 py-1.5 text-sm font-medium rounded-md transition-colors ${
      tab === t
        ? 'bg-indigo-600 text-white'
        : 'text-slate-400 hover:text-slate-100'
    }`

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="sticky top-0 z-10 bg-slate-950 border-b border-slate-800 px-6 py-4">
        <div className="flex flex-wrap gap-4 items-end justify-between">
          <form onSubmit={handleSubmit} className="flex gap-3 items-end flex-wrap">
            <span className="text-lg font-bold tracking-tight mr-2">neon</span>
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
            <button type="submit" className="bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium px-4 py-1.5 rounded">
              Load
            </button>
          </form>
          <div className="flex gap-1 bg-slate-900 rounded-lg p-1">
            <button className={tabClass('analytics')} onClick={() => setTab('analytics')}>Analytics</button>
            <button className={tabClass('payoff')} onClick={() => setTab('payoff')}>Payoff</button>
          </div>
        </div>
      </header>

      {tab === 'analytics' && (
        <main className="p-6 grid grid-cols-1 lg:grid-cols-2 gap-5">
          <Panel title={`${ticker} — 1Y Price`}>
            <PriceChart ticker={ticker} onSpot={setSpot} />
          </Panel>

          <Panel title={`${ticker} — Vol Surface (SVI)`}>
            <VolSurface ticker={ticker} />
          </Panel>

          {expiry && (
            <>
              <Panel title={`Options Chain — ${expiry}`}>
                <OptionsChain ticker={ticker} expiry={expiry} />
              </Panel>

              <Panel title={`IV Smile — ${expiry}`}>
                <IVSmile ticker={ticker} expiry={expiry} />
              </Panel>

              <Panel title={`Greeks Table — ${expiry}`}>
                <GreeksTable ticker={ticker} expiry={expiry} />
              </Panel>

              <div className="grid grid-rows-3 gap-5">
                <Panel title={`Delta — ${expiry}`}>
                  <DeltaSmile ticker={ticker} expiry={expiry} />
                </Panel>
                <Panel title={`Gamma — ${expiry}`}>
                  <GammaSmile ticker={ticker} expiry={expiry} />
                </Panel>
                <Panel title={`Theta — ${expiry}`}>
                  <ThetaSmile ticker={ticker} expiry={expiry} />
                </Panel>
              </div>
            </>
          )}

          <div className="lg:col-span-2">
            <Panel title="Portfolio Greeks">
              <PortfolioGreeks />
            </Panel>
          </div>

          <div className="lg:col-span-2">
            <Panel title="Bond Analytics">
              <BondAnalytics />
            </Panel>
          </div>
        </main>
      )}

      {tab === 'payoff' && (
        <main className="p-6">
          <Panel title="Option Payoff">
            <PayoffChart spot={spot} />
          </Panel>
        </main>
      )}
    </div>
  )
}
