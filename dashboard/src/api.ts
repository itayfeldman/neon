import axios from 'axios'

const http = axios.create({ baseURL: '/stock' })

export interface HistoryResponse {
  dates: string[]
  opens: number[]
  highs: number[]
  lows: number[]
  closes: number[]
  volumes: number[]
}

export interface OptionRow {
  strike: number
  iv: number
  bid: number
  ask: number
  volume: number
  option_type: 'call' | 'put'
}

export interface OptionsResponse {
  calls: OptionRow[]
  puts: OptionRow[]
}

export interface GreeksRow {
  strike: number
  option_type: 'call' | 'put'
  delta: number
  gamma: number
  vega: number
  theta: number
}

export interface GreeksResponse {
  rows: GreeksRow[]
}

export const fetchHistory = (ticker: string, period = '1y') =>
  http.get<HistoryResponse>(`/${ticker}/history`, { params: { period } }).then(r => r.data)

export const fetchOptions = (ticker: string, expiry: string) =>
  http.get<OptionsResponse>(`/${ticker}/options/${expiry}`).then(r => r.data)

export const fetchGreeks = (ticker: string, expiry: string) =>
  http.get<GreeksResponse>(`/${ticker}/greeks/${expiry}`).then(r => r.data)
