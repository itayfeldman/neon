import { useQuery } from '@tanstack/react-query'
import { Component, type ReactNode } from 'react'
// eslint-disable-next-line @typescript-eslint/no-explicit-any
import _factory from 'react-plotly.js/factory'
// plotly-gl3d is browser-only; excluded from Vite pre-bundling via optimizeDeps.exclude
import Plotly from 'plotly.js/dist/plotly-gl3d'
import { fetchSviSurface } from '../api'

// CJS interop: factory.js exports { default: fn }, not fn directly
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const createPlotlyComponent = (_factory as any).default ?? _factory
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const Plot = createPlotlyComponent(Plotly as any)

interface ErrorBoundaryState { error: boolean }

class PlotErrorBoundary extends Component<{ children: ReactNode }, ErrorBoundaryState> {
  state = { error: false }
  static getDerivedStateFromError() { return { error: true } }
  render() {
    if (this.state.error) return <div className="text-red-400">Chart failed to render.</div>
    return this.props.children
  }
}

interface Props {
  ticker: string
}

export function VolSurface({ ticker }: Props) {
  const { data, isPending, isError } = useQuery({
    queryKey: ['svi-surface', ticker],
    queryFn: () => fetchSviSurface(ticker),
  })

  if (isPending) return <div className="text-slate-400">Loading…</div>
  if (isError) return <div className="text-red-400">Failed to load vol surface.</div>

  const z = data.vols.map(row => row.map(v => +(v * 100).toFixed(2)))

  return (
    <PlotErrorBoundary>
      <Plot
        data={[{
          type: 'surface',
          x: data.expiries,
          y: data.strikes,
          z,
          colorscale: 'Viridis',
          showscale: true,
          colorbar: { tickfont: { color: '#94a3b8' } },
        }]}
        layout={{
          autosize: true,
          paper_bgcolor: 'transparent',
          plot_bgcolor: 'transparent',
          scene: {
            xaxis: { title: { text: 'Expiry' }, color: '#94a3b8', gridcolor: '#1e293b' },
            yaxis: { title: { text: 'Strike' }, color: '#94a3b8', gridcolor: '#1e293b' },
            zaxis: { title: { text: 'IV %' }, color: '#94a3b8', gridcolor: '#1e293b' },
            bgcolor: 'transparent',
          },
          margin: { l: 0, r: 0, t: 0, b: 0 },
          font: { color: '#94a3b8' },
        }}
        style={{ width: '100%', height: '340px' }}
        config={{ displayModeBar: false, responsive: true }}
      />
    </PlotErrorBoundary>
  )
}
