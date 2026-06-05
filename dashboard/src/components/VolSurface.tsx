import { useEffect, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchSviSurface } from '../api'

declare const Plotly: {
  newPlot: (el: HTMLElement, data: unknown[], layout: unknown, config?: unknown) => void
  purge: (el: HTMLElement) => void
}

interface Props {
  ticker: string
}

export function VolSurface({ ticker }: Props) {
  const ref = useRef<HTMLDivElement>(null)

  const { data, isPending, isError } = useQuery({
    queryKey: ['svi-surface', ticker],
    queryFn: () => fetchSviSurface(ticker),
  })

  useEffect(() => {
    if (!data || !ref.current) return
    const el = ref.current
    const z = data.vols.map(row => row.map(v => +(v * 100).toFixed(2)))

    Plotly.newPlot(el, [{
      type: 'surface',
      x: data.expiries,
      y: data.strikes,
      z,
      colorscale: 'Viridis',
      showscale: true,
      colorbar: { tickfont: { color: '#94a3b8' } },
    }], {
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
    }, { displayModeBar: false, responsive: true })

    return () => { Plotly.purge(el) }
  }, [data])

  if (isPending) return <div className="text-slate-400">Loading…</div>
  if (isError) return <div className="text-red-400">Failed to load vol surface.</div>

  return <div ref={ref} style={{ width: '100%', height: '340px' }} />
}
