import { useQuery } from '@tanstack/react-query'
import Plot from 'react-plotly.js'
import { fetchSviSurface } from '../api'

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
  )
}
